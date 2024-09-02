import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import List, Dict
import shutil

logger = logging.getLogger("root")


@dataclass
class SubModule:
    acceptors: List[dict]
    senders: List[dict]
    intents: list[dict]
    extensions: List[dict]


@dataclass
class Settings:
    version: str
    is_active: bool
    config: dict
    require_modules: list

    @staticmethod
    def from_dict(data):
        settings = Settings(
            version=data["version"],
            is_active=data["is_active"],
            config=data["config"],
            require_modules=data["require_modules"] if "require_modules" in data else [],
        )
        return settings


class Module:
    def __init__(self, name):
        self.acceptor_queues = None
        self.senders_queues = None
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
            self.settings: Settings = Settings.from_dict(json.load(file))

        if not self.settings.is_active:
            return

        self.module: SubModule = getattr(__import__(f"modules.{self.name}.main"), self.name).main

        self.intents = {}
        self.version = self.settings.version

    async def init_senders(self):
        self.senders_queues = {
            i["name"]: asyncio.Queue() for i in self.module.senders
        }

        for sender in self.module.senders:
            asyncio.run_coroutine_threadsafe(
                coro=sender["function"](**self.settings.config, queue=self.senders_queues[sender["name"]]),
                loop=asyncio.get_running_loop()
            )

    async def init_acceptors(self):
        self.acceptor_queues = {
            i["name"]: asyncio.Queue() for i in self.module.acceptors
        }

        for acceptor in self.module.acceptors:
            asyncio.run_coroutine_threadsafe(
                coro=acceptor["function"](**self.settings.config, queue=self.acceptor_queues[acceptor["name"]]),
                loop=asyncio.get_running_loop()
            )

    def get_intents(self):
        return self.module.intents

    def get_settings(self):
        return self.settings

    def get_extensions(self):
        return self.module.extensions

    def get_senders_queues(self):
        return self.senders_queues

    def get_acceptor_queues(self):
        return self.acceptor_queues

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
        self.intents = {}
        self.extensions = {}
        self.senders_queues: Dict[str, asyncio.Queue] = {}
        self.acceptor_queues: Dict[str, asyncio.Queue] = {}

    def init_modules(self):
        logger.debug("инициализация модулей...")
        for module_name in self.name_list:
            module = Module(name=module_name)

            if not module:
                logger.debug(f"модуль {module_name} НЕ инициализирован")
                continue

            if not module.settings.is_active:
                continue

            if module.settings.require_modules:
                for require_module in module.settings.require_modules:
                    if require_module not in self.name_list:  # TODO: сделать нормальную проверку
                        module.settings.is_active = False
                        logger.error(f"Required module '{require_module}' for module {module_name} not found")
                        continue

            self.modules[module_name] = module

            if hasattr(self.modules[module_name].module, "intents"):
                for intent in self.modules[module_name].get_intents():
                    self.intents[intent["name"]] = intent

            if hasattr(self.modules[module_name].module, "extensions"):
                for extension in self.modules[module_name].get_extensions():
                    self.extensions[extension["name"]] = extension["function"]

            logger.debug(f"модуль {module_name} инициализирован")

        logger.debug("модули инициализированы")

    async def run_queues(self):
        for module in self.modules.values():
            if not module.settings.is_active:
                continue

            if hasattr(module.module, "acceptors"):
                await module.init_acceptors()
                self.acceptor_queues.update(module.get_acceptor_queues())

            if hasattr(module.module, "senders"):
                await module.init_senders()
                self.senders_queues.update(module.get_senders_queues())

        logger.debug("очереди созданы")

    def get_extension(self, name):
        return self.extensions[name]

    def get_senders_queues(self):
        return self.senders_queues

    def get_acceptor_queues(self):
        return self.acceptor_queues

    def list_modules(self) -> List[str]:
        return list(self.modules.keys())

    def get_module_names(self):
        return self.name_list.copy()

    def reinit_module(self, name):
        pass
