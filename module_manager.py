import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import List, Dict
import shutil

from event import Event, EventTypes
from utils import SubModule, Settings, ModuleQueues

logger = logging.getLogger(__name__)


class Intent:
    def __init__(
            self,
            name: str,
            examples: List[str],
            queue: str = None,
            purpose: str = None,
            function: callable = None
    ):
        self.name = name
        self.examples = examples
        if (function and queue) or (not function and not queue):
            logger.warning(f"""Rule "{name}" contain error queue or function and can not to be executed""")
            self.function = None
            self.queue = None
            self.purpose = None
        else:
            self.queue = queue
            self.purpose = purpose
            self.function = function

    async def run(self, event: Event, mm: 'ModuleManager'):
        if self.function:
            if asyncio.iscoroutinefunction(self.function):
                await self.function(event)
            else:
                self.function(event)
            return

        if self.queue:
            event.event_type = EventTypes.text
            if self.purpose:
                event.purpose = self.purpose
            await mm.get_acceptor_queues()[self.queue].put(event)


class Module:
    def __init__(self, name):
        self.queues: ModuleQueues = ModuleQueues()
        self.name = name
        if not os.path.isfile(f"modules/{self.name}/settings.json"):
            if os.path.isfile(f"modules/{self.name}/example.settings.json"):
                shutil.copyfile(
                    src=f"modules/{self.name}/example.settings.json",
                    dst=f"modules/{self.name}/settings.json"
                )
            else:
                print(f"modules/{self.name}/settings.json not found, module {self.name} not init")
                return

        with open(f"modules/{self.name}/settings.json", "r", encoding="utf-8") as file:
            self.settings = Settings.from_dict(json.load(file))

        if not self.settings.is_active:
            return

        self.module: SubModule = getattr(__import__(f"modules.{self.name}.main"), self.name).main

        if not hasattr(self.module, "acceptor"):
            self.module.acceptor = None
        if not hasattr(self.module, "sender"):
            self.module.sender = None
        if not hasattr(self.module, "intents"):
            self.module.intents = None
        if not hasattr(self.module, "extensions"):
            self.module.extensions = None


        self.version = self.settings.version

    async def init(self):
        if hasattr(self.module, "init"):
            if asyncio.iscoroutinefunction(self.module.init):
                await self.module.init(**self.settings.as_dict)
            else:
                self.module.init(**self.settings.as_dict)

    async def run(self):
        if self.module.sender:
            asyncio.run_coroutine_threadsafe(
                coro=self.module.sender(queue=self.queues.output, config=self.settings.as_dict),
                loop=asyncio.get_running_loop()
            )
        if self.module.acceptor:
            asyncio.run_coroutine_threadsafe(
                coro=self.module.acceptor(queue=self.queues.input, config=self.settings.as_dict),
                loop=asyncio.get_running_loop()
            )

    # async def init_senders(self):
    #     self.senders_queues = {
    #         i["name"]: asyncio.Queue() for i in self.module.senders
    #     }
    #
    #     for sender in self.module.senders:
    #         asyncio.run_coroutine_threadsafe(
    #             coro=sender["function"](**self.settings.config, queue=self.senders_queues[sender["name"]]),
    #             loop=asyncio.get_running_loop()
    #         )
    #
    # async def init_acceptors(self):
    #     self.acceptor_queues = {
    #         i["name"]: asyncio.Queue() for i in self.module.acceptors
    #     }
    #
    #     for acceptor in self.module.acceptors:
    #         asyncio.run_coroutine_threadsafe(
    #             coro=acceptor["function"](**self.settings.config, queue=self.acceptor_queues[acceptor["name"]]),
    #             loop=asyncio.get_running_loop()
    #         )

    def get_intents(self):
        return self.module.intents

    def get_settings(self):
        return self.settings

    def get_extensions(self):
        return self.module.extensions
    #
    # def get_senders_queues(self):
    #     return self.senders_queues
    #
    # def get_acceptor_queues(self):
    #     return self.acceptor_queues

    def save_settings(self):
        with open(f"modules/{self.name}/settings.json", "w", encoding="utf-8") as file:
            json.dump(self.settings, file, ensure_ascii=False, indent=2)

    def run_intent(self):
        pass

    def __bool__(self):
        if hasattr(self, "settings"):
            return self.settings.is_active
        return False


class ModuleManager:
    def __init__(self):
        self.name_list = [dir_name for dir_name in os.listdir("modules") if os.path.isdir(f"modules/{dir_name}")]
        self.modules: Dict[str, Module] = {}
        self.intents = []
        self.extensions = {}

    def init_modules(self):
        logger.debug("инициализация модулей...")
        # TODO: Перенести в класс модуля
        remove_names = []
        for module_name in self.name_list:
            module = Module(name=module_name)

            if not module or not module.settings.is_active:
                logger.debug(f"модуль {module_name} НЕ инициализирован")
                #self.name_list.remove(module_name)
                #self.modules[module_name] = None
                remove_names.append(module_name)
                continue


            if module.settings.require_modules:
                for require_module in module.settings.require_modules:
                    if require_module not in self.name_list:  # TODO: сделать нормальную проверку
                        module.settings.is_active = False
                        logger.error(f"Required module '{require_module}' for module {module_name} not found")
                        continue

            self.modules[module_name] = module

            if self.modules[module_name].module.intents:
                for intent in self.modules[module_name].get_intents():
                    self.intents.append(intent)

            if self.modules[module_name].module.extensions:
                for extension in self.modules[module_name].get_extensions():
                    self.extensions[extension["name"]] = extension["function"]

            logger.debug(f"модуль {module_name} инициализирован")

        for name in remove_names:
            self.name_list.remove(name)

        logger.debug("модули инициализированы")

    async def run_queues(self):
        for module in self.modules.values():
            if not module.settings.is_active:
                continue

            await module.init()

        for module_name in self.name_list:
            await self.modules[module_name].run()

        logger.debug("очереди созданы")

    @property
    def queues(self):
        queues = {}
        for module_name in self.name_list:
            queues[module_name] = self.modules[module_name].queues

        return queues

    def get_extension(self, name):
        return self.extensions[name]

    def list_modules(self) -> List[str]:
        return self.name_list.copy()

    def get_module_names(self):
        return self.name_list.copy()

    def reinit_module(self, name):
        pass

    def get_module(self, module_name):
        pass

    async def _get_event(self, name: str = None):
        if not self.queues[name].output.empty():
            event = await self.queues[name].output.get()
            return event

    async def _put_event(self, event, name: str = None):
        await self.queues[name].input.put(event)
