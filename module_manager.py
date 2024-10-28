import asyncio
import json
import logging
import os
from typing import List, Dict
import shutil

from event import Event, EventTypes
from utils import SubModule, Settings, ModuleQueues

logger = logging.getLogger(__name__)


class Module:
    def __init__(self, name):
        self.name = name
        self.queues: ModuleQueues = ModuleQueues(name=self.name)
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
        self._event_loop: asyncio.AbstractEventLoop = None

    async def init(self):
        self._event_loop = asyncio.new_event_loop()

        if hasattr(self.module, "init"):
            try:
                if asyncio.iscoroutinefunction(self.module.init):
                    await self.module.init(config=self.settings.as_dict)
                else:
                    self.module.init(config=self.settings.as_dict)
            except Exception as e:
                logger.error(f"Error while initializing module {self.name}: {e}", exc_info=True)

    async def run(self):
        if self.module.sender:
            asyncio.run_coroutine_threadsafe(
                coro=self.module.sender(queue=self.queues.output, config=self.settings.as_dict),
                loop=self._event_loop
            )
        if self.module.acceptor:
            asyncio.run_coroutine_threadsafe(
                coro=self.module.acceptor(queue=self.queues.input, config=self.settings.as_dict),
                loop=self._event_loop
            )

    def get_intents(self):
        return self.module.intents

    async def stop(self):
        self._event_loop.stop()
        # self._event_loop.close()

    def get_settings(self):
        return self.settings

    def get_extensions(self):
        return self.module.extensions

    def save_settings(self):
        with open(f"modules/{self.name}/settings.json", "w", encoding="utf-8") as file:
            json.dump(self.settings, file, ensure_ascii=False, indent=2)

    def __bool__(self):
        if hasattr(self, "settings"):
            return self.settings.is_active
        return False


class ModuleManager:
    def __init__(self):
        self.name_list = [dir_name for dir_name in os.listdir("modules") if
                          os.path.isdir(f"modules/{dir_name}") and not dir_name.startswith("__")]
        self.modules: Dict[str, Module] = {}
        self.intents = []
        self.extensions = {}
        self._queues = None

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
        if not self._queues:
            self._queues = {}
            for module_name in self.name_list:
                self._queues[module_name] = self.modules[module_name].queues

        return self._queues

    def reinit_module(self, name):
        pass

    def get_module(self, module_name):
        pass

    # async def _get_event(self, name: str = None):
    #     if not self.queues[name].output.empty():
    #         event = await self.queues[name].output.get()
    #         return event
    #
    # async def _put_event(self, event, name: str = None):
    #     await self.queues[name].input.put(event)
