import asyncio
import os.path
from typing import List, Dict

from config import config_loader, Connection, IOPair
from event import EventTypes, Event
from module_manager import ModuleManager
from nlu import NLU
import logging

from utils.classes import Context, Intent

logging.basicConfig(
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger("root")
v = "0.1"


class Core:
    def __init__(self, connection_config_path="connections/config.yml"):
        self.MM = ModuleManager()
        self.nlu: NLU = None
        config = config_loader(connection_config_path)
        self.connection_rules = config["rules"]
        self.io_pairs = config["io_pairs"]
        self._intent_examples = {}
        self.intents: List[Intent] = None
        self.contexts: Dict[str, Context] = {}

    def init(self):
        self.MM.init_modules()

        for module in self.MM.name_list:
            if os.path.isfile(module_conn := f"modules/{module}/config.yml"):
                module_config = config_loader(module_conn)
                self.connection_rules.extend(module_config["rules"])
                self.io_pairs.extend(module_config["io_pairs"])
                self._intent_examples.update(module_config["intent_examples"])

        self._init_ext()

        if len(self.MM.intents) > 1:
            self.intents = [Intent(**i) for i in self.MM.intents] #{name: intent_data["examples"] for name, intent_data in self.MM.intents.items()}

            self.nlu = NLU(
                intents={intent.name: self._intent_examples[intent.name] for intent in self.intents},
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
        intent = self.nlu.classify_text(text=command_str, minimum_percent=0.7)

        if not len(intent):
            await event.reply("Команда не найдена.")
            return

        logger.debug(f"intent: {intent}")
        intent_name = intent[0][0]

        intent: List[Intent] = list(filter(lambda intent: intent.name == intent_name, self.intents))
        if len(intent) == 1:
            asyncio.run_coroutine_threadsafe(
                coro=intent[0].run(event, self.MM),
                loop=asyncio.get_running_loop()
            )

        logger.debug(f"command: {command_str} start")

    def get_out(self, name):
        for pair in self.io_pairs:
            if name == pair.destination:
                return self.MM.queues[pair.target].input
        else:
            return self.MM.queues[name].input

    async def run(self):
        await self.MM.run_queues()
        while True:
            await asyncio.sleep(0)
            for name, queues in self.MM.queues.items():
                if name in self.contexts:
                    continue

                sender_queue = queues.output
                if sender_queue.empty():
                    continue

                event = await sender_queue.get()
                # logger.debug(f"event: {event.value} принят")
                event.out_queue = self.get_out(name)

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
                end_context=await self.del_context(event=event),
                output=self.get_out(module_name)
            )

            await self.contexts[module_name].start()
        return setter

    async def del_context(self, event: Event):
        async def deleter():
            context = self.contexts.pop(event.from_module)
            await context.end()

        return deleter
