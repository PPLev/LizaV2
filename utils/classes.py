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
        if isinstance(value, Event):
            value.from_module = self.name

        return await super().put(value)


class ModuleQueues:
    def __init__(self, name:str):
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