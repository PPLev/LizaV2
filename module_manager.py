import asyncio
import json
import os
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class SubModule:
    acceptors: List[dict]
    senders: List[dict]
    intents: list[dict]


@dataclass
class Settings:
    version: str
    is_active: bool
    config: dict

    @staticmethod
    def from_dict(data):
        settings = Settings(
            version=data["version"],
            is_active=data["is_active"],
            config=data["config"],
        )
        return settings


class Module:
    def __init__(self, name):
        self.acceptor_queues = None
        self.senders_queues = None
        self.name = name
        if not os.path.isfile(f"modules/{self.name}/settings.json"):
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
            await asyncio.create_task(
                coro=sender["function"](**self.settings.config, queue=self.senders_queues[sender["name"]]),
                name=sender["name"]
            )

    async def init_acceptors(self):
        self.acceptor_queues = {
            i["name"]: asyncio.Queue() for i in self.module.acceptors
        }

        for acceptor in self.module.acceptors:
            await asyncio.create_task(
                coro=acceptor["function"](**self.settings.config, queue=self.senders_queues[acceptor["name"]]),
                name=acceptor["name"]
            )

    def get_intents(self):
        return self.module.intents

    def get_settings(self):
        return self.settings

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

    def init_modules(self):
        for module_name in self.name_list:
            module = Module(name=module_name)

            if not module:
                continue

            self.modules[module_name] = module

            if not self.modules[module_name].settings.is_active:
                continue

            if hasattr(self.modules[module_name].module, "intents"):
                self.intents.extend(self.modules[module_name].get_intents())

    async def run_queues(self):
        for module in self.modules.values():
            if not module.settings.is_active:
                continue

            if hasattr(module.module, "acceptors"):
                await module.init_acceptors()

            if hasattr(module.module, "senders"):
                await module.init_senders()

    def get_modules(self):
        pass

    def reinit_module(self, name):
        pass
