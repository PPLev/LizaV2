import asyncio
import json
import os
from datetime import datetime

import caldav
from caldav import Calendar

from event import Event

client = None
calendar = None


def with_calendar(url=None, login=None, password=None):
    def calendar_client(func: callable) -> callable:
        async def wrapper(*args, **kwargs):
            global client
            global calendar
            if client is None:
                client = caldav.DAVClient(url, login, password)
                calendar = client.calendar(url=url)

            kwargs['calendar'] = calendar

            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return calendar_client


def add_event(event: Event, calendar: Calendar = None):
    data = json.loads(event.value)
    start = data['start']
    end = data['end']
    calendar.save_event(
        dtstart=datetime(start["year"], start["month"], start["day"], start["hour"], start["minute"]),
        dtend=datetime(end["year"], end["month"], end["day"], end["hour"], end["minute"]),
        summary=data["text"],
        rrule={},
    )


def get_events(calendar: Calendar, event: Event):
    pass


def init():
    url = "https://cloud.example.com/remote.php/dav/calendars/admin/personal/"
    client = caldav.DAVClient(url=url, username="admin", password=os.environ["CALENDAR_PASSWORD"])
    calendar = client.calendar(url=url)
    print(calendar)
    event = calendar.save_event(
        dtstart=datetime(2024, 9, 1, 20),
        dtend=datetime(2024, 9, 1, 21),
        summary="Do the needful",
        rrule={},
    )
    print(event)
    # events = calendar.events()
    # print(events)


if __name__ == '__main__':
    init()
