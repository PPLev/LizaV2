import asyncio
import json
import os


class Module:
    def __init__(self, name):
        self.name = name
        with open(f"{self.name}/settings.json", "r", encoding="utf-8") as file:
            self.settings: dict = json.load(file)

        self.module = __import__(f"modules.{self.name}.main")

        self.acceptor_queues = {
            i["name"]: asyncio.Queue() for i in self.module.acceptors
        }

        self.senders_queues = {
            i["name"]: asyncio.Queue() for i in self.module.senders
        }

        for worker in self.module.workers:
            asyncio.create_task(worker(**self.settings, **self.acceptor_queues, **self.senders_queues))

        self.intents = {}
        self.version = ""

    def get_settings(self):
        return self.settings.copy()

    def update_setting(self, key, value):
        pass

    def update_settings(self, new_settings: dict):
        for key, val in new_settings.items():
            self.update_setting(key=key, value=val)

    def save_settings(self):
        with open(f"modules/{self.name}/settings.json", "w", encoding="utf-8") as file:
            json.dump(self.settings, file, ensure_ascii=False)

    def run_intent(self):
        pass

class ModuleManager:
    def __init__(self):
        self.name_list = [dir_name for dir_name in os.listdir("modules") if os.path.isdir(f"modules/{dir_name}")]
        self.modules = {}

    def list(self):
        for module_name in self.name_list:
            pass

    async def init_modules(self):
        pass

    def get_modules(self):
        pass
