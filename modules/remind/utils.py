import asyncio

from event import Event
from .models import Note

sender_queue: asyncio.Queue = None
remind_queue: asyncio.Queue = None


async def precreate(event: Event):
    pass
    # TODO: отправить ивент через в гпт в создание напоминалки


purpose_map = {
    "add_note": Note.from_event,
    "pre_add_note": precreate
}


async def remind_acceptor(queue: asyncio.Queue, config: dict):
    global calendar_queue

    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()

            if event.purpose in purpose_map:
                await purpose_map[event.purpose](event)


async def remind_sender(queue: asyncio.Queue, config: dict):
    global sender_queue
    sender_queue = queue


def init():
    Note.create_table(safe=True)
