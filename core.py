import asyncio
from typing import List

from connection import Connection
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
    def __init__(self, connection_config_path="modules/connections.json"):
        self.queues = {}
        self.MM = ModuleManager()
        self.nlu: NLU = None
        self.connection_rules = Connection.load()

    def init(self):
        self.MM.init_modules()
        self._init_ext()
        self.nlu = NLU(
            intents={name: intent["examples"] for name, intent in self.MM.intents.items()}
        )

    def _init_ext(self):
        for connection in self.connection_rules:
            connection.init_extensions(self.MM)

    async def run_command(self, event: Event):
        if len(self.MM.intents) == 0:
            return

        command_str = event.value
        logger.debug(f"command: {command_str}")
        intent = self.nlu.classify_text(text=command_str)
        logger.debug(f"intent: {intent}")
        intent_name = intent[0][0]
        intent_function = self.MM.intents[intent_name]["function"]
        asyncio.run_coroutine_threadsafe(
            coro=intent_function(event),
            loop=asyncio.get_running_loop()
        )
        logger.debug(f"command: {command_str} start")

    async def run(self):
        await self.MM.run_queues()
        while True:
            await asyncio.sleep(0)
            for name, queue in self.MM.get_senders_queues().items():
                queue: asyncio.Queue
                if queue.empty():
                    continue

                event = await queue.get()

                if event.event_type == EventTypes.user_command:
                    await asyncio.create_task(
                        coro=self.run_command(event=event)
                    )

                if event.event_type == EventTypes.text:
                    connections: List[Connection] = filter(lambda x: name in x.senders, self.connection_rules)
                    for connection in connections:
                        asyncio.run_coroutine_threadsafe(
                            coro=connection.run_event(event=event.copy(), mm=self.MM), loop=asyncio.get_event_loop()
                        )
