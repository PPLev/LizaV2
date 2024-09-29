from event import Event
from .models import Note


def on_startup():
    Note.create_table(safe=True)


async def precreate(event: Event):
    pass