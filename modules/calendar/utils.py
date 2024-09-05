import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
import logging
import caldav

from event import Event

logger = logging.getLogger(__name__)

@dataclass
class CalendarData:
    url: str
    username: str
    password: str


calendar_data: CalendarData = None


# def with_calendar(url=None, login=None, password=None):
#     def calendar_client(func: callable) -> callable:
#         async def wrapper(*args, **kwargs):
#             global client
#             global calendar
#             if client is None:
#                 client = caldav.DAVClient(url, login, password)
#                 calendar = client.calendar(url=url)
#
#             kwargs['calendar'] = calendar
#
#             if asyncio.iscoroutinefunction(func):
#                 return await func(*args, **kwargs)
#             else:
#                 return func(*args, **kwargs)
#
#         return wrapper
#
#     return calendar_client


async def add_event(url: str, username: str, password: str, queue: asyncio.Queue = None, **kwargs):
    client = caldav.DAVClient(url=url, username=username, password=password)
    calendar = client.calendar(url=url)

    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()
            logger.debug(f"Calendar get event {event.value}")
            data = json.loads(event.value)
            start = data['start']
            end = data['end']
            start_date = datetime(start["year"], start["month"], start["day"], start["hour"], start["minute"])
            if end:
                end_date = datetime(end["year"], end["month"], end["day"], end["hour"], end["minute"])
            else:
                end_date = start_date
            try:
                calendar.save_event(
                    dtstart=start_date,
                    dtend=end_date,
                    summary=data["text"],
                    rrule={},
                )
                await event.reply(
                    f"""Событие "{data['text']}" на {start["month"]}.{start["day"]} """ +
                    f"""в {start["hour"]}:{start["minute"]} добавлено."""
                )
            except Exception as e:
                logger.error(f"Calendar add_event error: {e}", exc_info=True)

#
# def get_events(calendar: Calendar, event: Event):
#     pass


def init(url=None, username=None, password=None):
    global calendar_data
    calendar_data = CalendarData(url, username, password)
