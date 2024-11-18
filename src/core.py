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


class CoreAlreadyRunningException(Exception):
    pass


class Core:
    """
    Ядро Liza.

    Ядро обрабатывает ивенты из очередей и взаимодействует с модульменеджером для работы с модулями.
    """
    def __init__(
            self,
            connection_config_path="connections/config.yml",
            minimum_nlu_percent=0.69,
            forward_core_events=True,
    ):
        """
        Инициализация класса с настройками соединения и параметрами обработки NLU.

        :param connection_config_path:  Путь к файлу конфигурации соединения (по умолчанию "connections/config.yml").
        :param minimum_nlu_percent: Минимально допустимый процент уверенности NLU для определения успешного распознавания намерения (по умолчанию 0.69).
        :param forward_core_events: Указывает, должны ли основные события передаваться дальше в обработку (по умолчанию True).
        """
        self.MM = ModuleManager()
        self.nlu: NLU = None
        self.min_nlu_percent = minimum_nlu_percent
        config = config_loader(connection_config_path)
        self.connection_rules = config["rules"]
        self.io_pairs = config["io_pairs"]
        self._intent_examples = {}
        self.intents: List[Intent] = None
        self.contexts: Dict[str, Context] = {}
        self._is_running = False
        self.forward_core_events = forward_core_events

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
            self.intents = [Intent(**i) for i in self.MM.intents]

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
        intent = self.nlu.classify_text(text=command_str, minimum_percent=self.min_nlu_percent)

        if not len(intent):
            await event.reply("Команда не найдена.")
            return

        logger.debug(f"intent: {intent}")
        intent_name = intent[0][0]

        intent: List[Intent] = list(filter(lambda intent: intent.name == intent_name, self.intents))
        if len(intent) == 1:
            await asyncio.create_task(intent[0].run(event, self.MM))

        logger.debug(f"command: {command_str} start")

    def get_out_queues(self, name):
        for pair in self.io_pairs:
            if name == pair.destination:
                return self.MM.queues[pair.target].input
        else:
            return self.MM.queues[name].input

    async def core_query(self, event: Event):
        def reply(data):
            async def wrapper():
                if hasattr(event, "callback"):
                    await event.callback(data)
                else:
                    await event.reply(data)
            return wrapper

        commands = {
            "get_modules": reply(self.MM.name_list),
            "get_extensions": reply(self.MM.extensions.keys()),
            "get_intents": reply(self.nlu.intents),
        }
        if event.value not in commands.keys():
            await reply(f"Query not found in [{commands.keys()}]")()
        else:
            await commands[event.value]()

    async def run_event(self, event: Event):
        logger.debug(f'event: "{event.value}" принят')

        if event.event_type == EventTypes.user_command:
            event.set_context = self.get_context_setter(event=event)
            asyncio.run_coroutine_threadsafe(
                coro=self.run_command(event=event),
                loop=asyncio.get_running_loop()
            )

        elif event.event_type == EventTypes.text:
            for connection in self.connection_rules:
                asyncio.run_coroutine_threadsafe(
                    coro=connection.run_event(event=event.copy(), mm=self.MM),
                    loop=asyncio.get_running_loop()
                )

        elif event.event_type == EventTypes.core_query:
            await self.core_query(event)

        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    async def run(self):
        if self._is_running:
            logger.error("Error running core, core already running")
            raise CoreAlreadyRunningException

        self.MM.add_named_queues("core")
        await self.MM.run_modules()

        self._is_running = True
        while True:
            await asyncio.sleep(0)

            if self.forward_core_events:
                if not self.MM.queues["core"].input.empty():
                    while not self.MM.queues["core"].input.empty():
                        event = await self.MM.queues["core"].input.get()
                        await self.MM.queues["core"].output.put(event)

            for name, queues in self.MM.queues.items():
                if name in self.contexts:
                    continue

                sender_queue = queues.output
                if sender_queue.empty():
                    continue

                event = await sender_queue.get()
                if event.out_queue is None:
                    event.out_queue = self.get_out_queues(name)

                await self.run_event(event)

    async def get_module(self, module_name):
        return self.MM.get_module(module_name)

    def get_context_setter(self, event: Event):
        async def setter(callback: callable, init_context_data: dict = None):
            module_name = event.from_module
            if module_name in self.contexts:
                raise Exception("Duplicate context, end exist context before create new context")

            self.contexts[module_name] = Context(
                module_queue=self.MM.queues[module_name],
                callback=callback,
                init_context_data=init_context_data,
                end_context=await self.get_context_deleter(event=event),
                output=self.get_out_queues(module_name)
            )

            await self.contexts[module_name].start()

        return setter

    async def get_context_deleter(self, event: Event):
        async def deleter():
            context = self.contexts.pop(event.from_module)
            await context.end()

        return deleter

    async def wait_for_run(self):
        while not self._is_running:
            await asyncio.sleep(0)

    @property
    def is_running(self):
        return self._is_running