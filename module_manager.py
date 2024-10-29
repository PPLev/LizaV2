import asyncio
import json
import logging
import os
import sys
from typing import Dict
import shutil
from importlib import reload, import_module, invalidate_caches
from utils import SubModule, Settings, ModuleQueues

logger = logging.getLogger(__name__)


def return_blank_list_if_not_active(func: callable) -> callable:
    def wrapper(obj, *args, **kwargs):
        if obj.settings.is_active:
            return func(obj, *args, **kwargs)
        return []

    return wrapper


class Module:
    def __init__(self, name, mm: 'ModuleManager'):
        self.name = name
        self.module: SubModule = None
        self.queues: ModuleQueues = ModuleQueues(name=self.name)
        if not os.path.isfile(f"modules/{self.name}/settings.json"):
            if os.path.isfile(f"modules/{self.name}/example.settings.json"):
                shutil.copyfile(
                    src=f"modules/{self.name}/example.settings.json",
                    dst=f"modules/{self.name}/settings.json"
                )
            else:
                logger.error(
                    f"modules/{self.name}/settings.json и "
                    f"modules/{self.name}/example.settings.json не найдены, "
                    f"невозможно инициализировать {self.name}"
                )
                self.settings = Settings(
                    version=0.0,
                    is_active=False,
                    config={},
                    require_modules=[],
                )
                return

        with open(f"modules/{self.name}/settings.json", "r", encoding="utf-8") as file:
            self.settings = Settings.from_dict(json.load(file))

        if not self.settings.is_active:
            logger.debug(f"Модуль {self.name} выключен")

        try:
            if self.name in mm.modules.keys():
                invalidate_caches()
                self.module = reload(module=mm.modules[self.name].module)
            else:
                self.module: SubModule = import_module(f"modules.{self.name}.main")

        except ModuleNotFoundError:
            self.settings.is_active = False
            logger.error(
                f"Модуль {self.name}.main или его зависимости не найдены, невозможно инициализировать {self.name}",
                exc_info=True
            )
            return

        if not hasattr(self.module, "acceptor"):
            self.module.acceptor = None
        if not hasattr(self.module, "sender"):
            self.module.sender = None
        if not hasattr(self.module, "intents"):
            self.module.intents = []
        if not hasattr(self.module, "extensions"):
            self.module.extensions = []

        self.version = self.settings.version
        self._mm = mm

        self.acceptor_task: asyncio.Task = None
        self.sender_task: asyncio.Task = None

    async def init(self):
        if not self.settings.is_active:
            return

        if hasattr(self.module, "init"):
            try:
                if asyncio.iscoroutinefunction(self.module.init):
                    await self.module.init(config=self.settings.as_dict)
                else:
                    self.module.init(config=self.settings.as_dict)
            except Exception as e:
                logger.error(f"Error func init() in module {self.name}: {e}", exc_info=True)

    async def run(self):
        if not self.settings.is_active:
            return

        if self.module.sender:
            self.sender_task = asyncio.create_task(
                self.module.sender(queue=self.queues.output, config=self.settings.as_dict)
            )
        if self.module.acceptor:
            self.acceptor_task = asyncio.create_task(
                self.module.acceptor(queue=self.queues.input, config=self.settings.as_dict)
            )

    @return_blank_list_if_not_active
    def get_intents(self):
        return self.module.intents

    def stop(self):
        self.acceptor_task.cancel()
        self.sender_task.cancel()

    def get_settings(self):
        return self.settings

    @return_blank_list_if_not_active
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

    def _init_module(self, module_name: str):
        module = Module(name=module_name, mm=self)
        asyncio.gather(module.init())
        return module

    def init_module(self, module_name):
        module = self._init_module(module_name)
        # future = asyncio.run_coroutine_threadsafe(module.init(), asyncio.get_event_loop())
        # future.result()
        self.modules[module_name] = module
        if not module.settings.is_active:
            logger.debug(f"модуль {module_name} НЕ инициализирован")
            return

        if module.settings.require_modules:
            for require_module_name in module.settings.require_modules:
                if require_module_name not in self.name_list:
                    module.settings.is_active = False
                    logger.error(f"Required module '{require_module_name}' for module {module_name} not found")
                    continue

                if require_module_name not in self.modules.keys():
                    self.init_module(require_module_name)

                if not self.modules[require_module_name].settings.is_active:
                    module.settings.is_active = False
                    logger.error(f"Required module '{require_module_name}' for module {module_name} not active")
                    continue

        self.intents.extend(module.get_intents())

        for extension in module.get_extensions():
            self.extensions[extension["name"]] = extension["function"]

        logger.debug(f"модуль {module_name} инициализирован")

    def init_modules(self):
        logger.debug("инициализация модулей...")
        for module_name in self.name_list:
            if module_name not in self.modules.keys():
                self.init_module(module_name)

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

    def reload_module(self, name):
        self.modules[name].stop()
        self.init_module(name)

    def get_module(self, module_name):
        pass

    # async def _get_event(self, name: str = None):
    #     if not self.queues[name].output.empty():
    #         event = await self.queues[name].output.get()
    #         return event
    #
    # async def _put_event(self, event, name: str = None):
    #     await self.queues[name].input.put(event)
