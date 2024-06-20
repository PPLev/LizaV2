import asyncio
import json

from nlu import NLU


class Module:
    def __init__(self, name):
        self.name = name
        with open(f"{self.name}/settings.json", "r", encoding="utf-8") as file:
            self.settings = json.load(file)

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
        pass

    def update_settings(self, key, value):
        pass

    def run_intent(self):
        pass

class ModuleManager:
    def __init__(self):
        self.nlu: NLU = None

    def list(self):
        pass

    async def init_modules(self):
        pass

    def get_modules(self):
        pass
