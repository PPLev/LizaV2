import asyncio
import json

from event import EventTypes, Event
from module_manager import ModuleManager
from nlu import NLU
import logging

logging.basicConfig(
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger("root")
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

    def init(self):
        self.MM.init_modules()
        self.nlu = NLU(
            intents={intent["name"]: intent["examples"] for intent in self.MM.intents}
        )

    async def run(self):
        await self.MM.run_queues()
        while True:
            await asyncio.sleep(0)

    async def main_event_work(self, event: Event):
        if event.event_type == EventTypes.user_command:
            await asyncio.create_task(
                coro=self.run_command(event=event)
            )

        if event.event_type == EventTypes.text:
            pass

    async def run_command(self, event: Event):
        command_str = event.value
        logger.debug(f"command: {command_str}")
        #intent = self.nlu.classify_text(text=command_str)

    async def run(self):
        await self.MM.run_queues()
        while True:
            await asyncio.sleep(0)
            for name, queue in self.MM.get_senders_queues().items():
                queue: asyncio.Queue
                if queue.empty():
                    continue

                event = await queue.get()
                await asyncio.create_task(self.main_event_work(event=event))

            for name, queue in self.MM.get_acceptor_queues().items():
                queue: asyncio.Queue
                if queue.empty():
                    continue

                event = await queue.get()
                await asyncio.create_task(self.main_event_work(event=event))
