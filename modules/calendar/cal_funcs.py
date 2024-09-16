import calendar
import json
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


async def create_event(event: Event, calendar: caldav.Calendar):
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
            value=f"""Событие "{data['text']}" на """ +
            f"""{start["day"]}.{"0" + str(start["month"]) if start["month"] < 10 else "0"} """ +
            f"""в {start["hour"]}:{start["minute"]} добавлено.""",
            new_purpose="add_event_complete"
        )

    except Exception as e:
        logger.error(f"Calendar add_event error: {e}", exc_info=True)
