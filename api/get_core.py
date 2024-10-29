import asyncio
from typing import Annotated

from fastapi import Depends

from core import Core

core = Core()
core.init()
http_queue = asyncio.Queue()


def get_core() -> Core:
    yield core


CoreDep = Annotated[Core, Depends(get_core)]


def get_queue() -> asyncio.Queue:
    yield http_queue


HttpQueueDep = Annotated[asyncio.Queue, Depends(get_queue)]
