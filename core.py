import asyncio
import json

from event import EventTypes
from module_manager import ModuleManager
from nlu import NLU

v = "0.1"


class Core:
    def __init__(self, connection_config_path="modules/conections.json"):
        self.connection_data = None
        self.connection_config_path = connection_config_path
        self.queues = {}
        self.MM = ModuleManager()
        self.nlu: NLU = None
        with open(self.connection_config_path, "r", encoding="utf-8") as file:
            self.connection_data = json.load(file)

    async def run(self):
        self.MM.init_modules()

        while True:
            await asyncio.sleep(0)

    async def event_work(self, event):
        if event.event_type == EventTypes.text:
            pass

        if event.event_type == EventTypes.text:
            target_name = self.nlu.classify_text(event.value)
