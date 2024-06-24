import asyncio
import json
import os
from dataclasses import dataclass
from typing import List

@dataclass
class SubModule:
    acceptors: List[dict]
    senders: List[dict]
    intents: list[dict]


@dataclass
class Settings:
    version: str
    is_active: bool
    types: list
    config: dict

    @staticmethod
    def from_dict(data):
        settings = Settings(
            version=data["version"],
            is_active=data["is_active"],
            types=data["types"],
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

        if hasattr(self.module, "senders"):
            self.init_as_sender()

        if hasattr(self.module, "acceptors"):
            self.init_as_acceptor()

        self.intents = {}
        self.version = self.settings.version

    def init_as_sender(self):
        self.senders_queues = {
            i["name"]: asyncio.Queue() for i in self.module.senders
        }

        for sender in self.module.senders:
            asyncio.create_task(sender["function"](**self.settings.config, queue = self.senders_queues[sender["name"]]))

    def init_as_acceptor(self):
        self.acceptor_queues = {
            i["name"]: asyncio.Queue() for i in self.module.acceptors
        }

        for acceptor in self.module.acceptors:
            asyncio.create_task(acceptor["function"](**self.settings.config, queue = self.senders_queues[acceptor["name"]]))

    def get_settings(self):
        return self.settings

    def save_settings(self):
        with open(f"modules/{self.name}/settings.json", "w", encoding="utf-8") as file:
            json.dump(self.settings, file, ensure_ascii=False)

    def run_intent(self):
        pass

class ModuleManager:
    def __init__(self):
        self.name_list = [dir_name for dir_name in os.listdir("modules") if os.path.isdir(f"modules/{dir_name}")]
        self.modules = {}

    def init_modules(self):
        for module_name in self.name_list:
            self.modules[module_name] = Module(name=module_name)

    def get_modules(self):
        pass
    
    def reinit_module(self, name):
        pass