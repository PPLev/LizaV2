from event import Event
from .models import Note


def init():
    Note.create_table(safe=True)


async def precreate(event: Event):
    pass
    # TODO: отправить ивент через в гпт в создание напоминалки