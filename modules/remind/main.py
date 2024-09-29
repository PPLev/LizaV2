import asyncio
import os
import sys
import logging

from event import Event

logger = logging.getLogger("root")


async def test(event: Event):  # полный перезапуск
    pass


async def test_context_callback(event: Event):
    print(f"Дев модуль, ивент в контексте: {event.value}")

    if event.context["p"] == 1:
        await event.reply(event.value)
        event.context["p"] = 0

    elif event.context["p"] == 0:
        await event.reply(event.value+"end")
        await event.end_context()


async def test_acceptor(queue: asyncio.Queue, config: dict):
    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()

            #await event.set_context(callback=test_context_callback, init_context_data={"p": 1})
            await event.reply(event.value)


acceptor = test_acceptor

intents = [
    {
        "name": "test",
        "queue": "dev_module",
        "purpose": "test"
    }
]
