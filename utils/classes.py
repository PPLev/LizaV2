import asyncio
from dataclasses import dataclass
from typing import List, Dict

from event import Event


@dataclass
class SubModule:
    acceptor: callable
    sender: callable
    intents: list[dict]
    extensions: List[dict]


class AsyncModuleQueue(asyncio.Queue):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    async def put(self, value):
        if isinstance(value, Event) and value.from_module is None:
            value.from_module = self.name

        return await super().put(value)


class ModuleQueues:
    def __init__(self, name: str):
        self.input = AsyncModuleQueue(name, maxsize=50)
        self.output = AsyncModuleQueue(name, maxsize=50)


@dataclass
class Settings:
    def __init__(self, version, is_active, config, require_modules):
        self.version = version
        self.is_active = is_active
        self.config = config
        self.require_modules = require_modules

    @staticmethod
    def from_dict(data) -> 'Settings':
        settings = Settings(
            version=data["version"],
            is_active=data["is_active"],
            config=data["config"],
            require_modules=data["require_modules"] if "require_modules" in data else [],
        )
        return settings

    @property
    def as_dict(self) -> Dict:
        return self.config.copy()


class Context:
    def __init__(
            self,
            module_queue: ModuleQueues,
            init_context_data: Dict,
            callback: callable,
            end_context: callable,
            output: asyncio.Queue
    ):
        # TODO: переделать на взаимодействие через модуль менеджер
        self._data = init_context_data or {}
        self.module_queue = module_queue
        self.callback = callback
        self.end_context = end_context
        self.output = output
        self.__is_started = False

    async def start(self):
        self.__is_started = True
        asyncio.run_coroutine_threadsafe(
            coro=self.loop(),
            loop=asyncio.get_running_loop(),
        )

    async def loop(self):
        while self.__is_started:
            await asyncio.sleep(0)
            if not self.module_queue.output.empty():
                event = await self.module_queue.output.get()
                event.context = self._data
                event.out_queue = self.output
                event.end_context = self.end_context
                await self.callback(event)

    async def end(self):
        self.__is_started = False

    def update(self, data: dict):
        self._data.update(data)

    def get(self, key):
        return self._data.get(key)

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value
