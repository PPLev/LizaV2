import asyncio
import os.path
from typing import List, Dict

from connection import Connection, IOPair
from event import EventTypes, Event
from module_manager import ModuleManager, Intent
from nlu import NLU
import logging

from utils.classes import Context

logging.basicConfig(
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger("root")
v = "0.1"


class Core:
    def __init__(self, connection_config_path="connections/connections.yml"):
        self.MM = ModuleManager()
        self.nlu: NLU = None
        self.connection_rules = Connection.load_file(connection_config_path)
        self.io_pairs = IOPair.load_file(connection_config_path)
        self.intents: List[Intent] = None
        self.contexts: Dict[str, Context] = {}

        for module in self.MM.list_modules():
            if os.path.isfile(module_conn := f"modules/{module}/connections.yml"):
                self.connection_rules.extend(Connection.load_file(module_conn))
                self.io_pairs.extend(IOPair.load_file(module_conn))

    def init(self):
        self.MM.init_modules()
        self._init_ext()
        if len(self.MM.intents) > 1:
            self.intents = [Intent(**i) for i in self.MM.intents] #{name: intent_data["examples"] for name, intent_data in self.MM.intents.items()}
            self.nlu = NLU(
                intents={intent.name: intent.examples for intent in self.intents},
            )

    def _init_ext(self):
        for connection in self.connection_rules:
            try:
                connection.init_extensions(self.MM)
            except KeyError as e:
                logger.error(f"Ошибка правила {connection.name} расширение {e.args} не найдено")
                self.connection_rules.remove(connection)

    async def run_command(self, event: Event):
        if not self.nlu:
            return

        command_str = event.value
        logger.debug(f"command: {command_str}")
        intent = self.nlu.classify_text(text=command_str)
        logger.debug(f"intent: {intent}")
        intent_name = intent[0][0]

        intent: List[Intent] = list(filter(lambda intent: intent.name == intent_name, self.intents))
        if len(intent) == 1:
            asyncio.run_coroutine_threadsafe(
                coro=intent[0].run(event, self.MM),
                loop=asyncio.get_running_loop()
            )

        logger.debug(f"command: {command_str} start")

    # def

    async def run(self):
        await self.MM.run_queues()
        while True:
            await asyncio.sleep(0)
            for name, queues in self.MM.queues.items():
                # TODO: Переписать!!!
                if name in self.contexts:
                    for pair in self.io_pairs:
                        if name == pair.destination:
                            event.out_queue = self.MM.queues[pair.target].input
                            break
                    else:
                        event.out_queue = self.MM.queues[event.from_module].input

                    continue

                sender_queue = queues.output
                if sender_queue.empty():
                    continue

                event = await sender_queue.get()
                # logger.debug(f"event: {event.value} принят")

                for pair in self.io_pairs:
                    if name == pair.destination:
                        event.out_queue = self.MM.queues[pair.target].input
                        break
                else:
                    event.out_queue = self.MM.queues[event.from_module].input

                if event.event_type == EventTypes.user_command:
                    event.set_context = self.preconfigure_context(event=event)
                    await asyncio.create_task(
                        coro=self.run_command(event=event)
                    )

                if event.event_type == EventTypes.text:
                    for connection in self.connection_rules:
                        asyncio.run_coroutine_threadsafe(
                            coro=connection.run_event(event=event.copy(), mm=self.MM), loop=asyncio.get_event_loop()
                        )

    async def get_module(self, module_name):
        return self.MM.get_module(module_name)

    def preconfigure_context(self, event: Event):
        async def setter(callback: callable, init_context_data: dict=None):
            module_name = event.from_module
            if module_name in self.contexts:
                raise Exception("Duplicate context, end exist context before create new context")

            self.contexts[module_name] = Context(
                module_queue=self.MM.queues[module_name],
                callback=callback,
                init_context_data=init_context_data,
                end_context=await self.del_context(event=event)
            )

            await self.contexts[module_name].start()
        return setter

    async def del_context(self, event: Event):
        async def deleter():
            context = self.contexts.pop(event.from_module)
            await context.end()

        return deleter
