import asyncio
import contextvars
import logging
from dataclasses import dataclass, field
from functools import partial
from typing import List, Dict, Callable, Any, Set
import inspect
from event import Event, EventTypes

#from module_manager import ModuleManager


logger = logging.getLogger(__name__)


@dataclass
class SubModule:
    acceptor: callable
    sender: callable
    intents: list[dict]
    extensions: List[dict]


class Intent:
    def __init__(
            self,
            name: str,
            queue: str = None,
            purpose: str = None,
            function: callable = None
    ):
        self.name = name
        if (function and queue) or (not function and not queue):
            logger.warning(f"""Rule "{name}" contain error queue or function and can not to be executed""")
            self.function = None
            self.queue = None
            self.purpose = None
        else:
            self.queue = queue
            self.purpose = purpose
            self.function = function

    async def _run_func(self, event: Event):
        if asyncio.iscoroutinefunction(self.function):
            if "event" in inspect.getfullargspec(self.function).args:
                await self.function(event)
            else:
                await self.function()
        else:
            if "event" in inspect.getfullargspec(self.function).args:
                self.function(event)
            else:
                self.function()
        return

    async def run(self, event: Event, mm: 'ModuleManager'):
        if self.function:
            await self._run_func(event)
        if self.queue:
            event.event_type = EventTypes.text
            if self.purpose:
                event.purpose = self.purpose
            await mm.queues[self.queue].input.put(event)


class AsyncModuleQueue(asyncio.Queue):
    def __init__(self, name: str, is_active=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.is_active = is_active

    async def put(self, value):
        if not self.is_active:
            logger.error(f"Очередь {self.name} неактивна, возможно модуль выключен")
        if isinstance(value, Event) and value.from_module is None:
            value.from_module = self.name

        return await super().put(value)


class ModuleQueues:
    def __init__(self, name: str):
        self.input = AsyncModuleQueue(name, maxsize=50)
        self.output = AsyncModuleQueue(name, maxsize=50)

    def set_active(self):
        self.input.is_active = True
        self.input.is_active = True


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
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(event, self._data)
                else:
                    self.callback(event, self._data)

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


# TODO: использовать для вызова функций модуля
@dataclass
class CallableObject:
    callback: Callable[..., Any]
    awaitable: bool = field(init=False)
    params: Set[str] = field(init=False)
    varkw: bool = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        spec = inspect.getfullargspec(callback)
        self.params = {*spec.args, *spec.kwonlyargs}
        self.varkw = spec.varkw is not None

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.varkw:
            return kwargs

        return {k: kwargs[k] for k in self.params if k in kwargs}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()

        loop = asyncio.get_event_loop()
        context = contextvars.copy_context()
        wrapped = partial(context.run, wrapped)
        return await loop.run_in_executor(None, wrapped)
