import asyncio
import logging
import caldav
from .cal_funcs import create_event, CalendarData
from event import Event

logger = logging.getLogger(__name__)

calendar_data: CalendarData = None

calendar_queue: asyncio.Queue = None


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


async def cal_sender(queue: asyncio.Queue, config: dict):
    while True:
        await asyncio.sleep(0)
        if not calendar_queue.empty():
            event = await calendar_queue.get()
            #event.purpose = event.purpose.replace('pre_', '')
            await queue.put(event)


async def cal_acceptor(queue: asyncio.Queue, config: dict):
    global calendar_queue
    url = config["url"]
    username = config["username"]
    password = config["password"]

    client = caldav.DAVClient(url=url, username=username, password=password)
    calendar = client.calendar(url=url)

    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event: Event = await queue.get()

            if event.purpose == "add_event":
                await create_event(event, calendar)

            elif event.purpose == "pre_add_event":
                await calendar_queue.put(event)


#
# def get_events(calendar: Calendar, event: Event):
#     pass


def init(url=None, username=None, password=None):
    global calendar_data, calendar_queue
    calendar_queue = asyncio.Queue()
    calendar_data = CalendarData(url, username, password)
