import asyncio
import json

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
        with open(connection_config_path, "r", encoding="utf-8") as file:
            connection_data = json.load(file)
            self.connection_data = [Connection(**i) for i in connection_data["rules"]]

    def init(self):
        self.MM.init_modules()
        self.nlu = NLU(
            intents={name: intent["examples"] for name, intent in self.MM.intents.items()}
        )

    async def run_command(self, event: Event):
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
                    connections = filter(lambda x: x.sender == name, self.connection_data)
                    for connection in connections:
                        event_connection_allowed = False
                        is_event_purposed = hasattr(event, "purpose")
                        exec_purpose = bool(len(connection.allowed_purposes))

                        if exec_purpose and is_event_purposed:
                            if event.purpose in connection.allowed_purposes:
                                event_connection_allowed = True

                        else:
                            event_connection_allowed = True

                        if event_connection_allowed:
                            await self.MM.acceptor_queues[connection.acceptor].put(event)
