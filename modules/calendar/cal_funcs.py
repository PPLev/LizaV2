import calendar
import json
from dataclasses import dataclass
import datetime
import logging
from typing import List

import caldav
import ics
import icalendar
from event import Event

logger = logging.getLogger(__name__)


@dataclass
class CalendarData:
    url: str
    username: str
    password: str


def formated(event: ics.Event):
    return (f"Text: {event.name}  "
            f"start:{event.begin.strftime('%d.%m.%Y %H:%M')} "
            f"end:{event.end.strftime('%d.%m.%Y %H:%M')}")


class Calendar:
    tzinfo = datetime.datetime.now().tzinfo

    def __init__(self, url: str, username: str, password: str):
        self._client = caldav.DAVClient(url=url, username=username, password=password)
        self._calendar: caldav.Calendar = self._client.calendar(url=url)

    def create_event(self, value, start: datetime, end: datetime):
        self._calendar.save_event(
            dtstart=start,
            dtend=end,
            summary=value,
            rrule={},
        )

        #self._calendar.save_event(ical=)

    def get_events(
            self,
            start: datetime = datetime.datetime.now(),
            end: datetime = datetime.datetime.now() + datetime.timedelta(days=7)
    ) -> List[ics.Event]:
        events = self._calendar.search(
            start=start,
            end=end,
            event=True,
            expand=True,
        )
        filtered_events = []
        for event in events:
            ics_cal = ics.Calendar(event.data)
            ics_event = list(ics_cal.events)[0]
            ics_event.begin = ics_event.begin.astimezone(tz=self.tzinfo)
            ics_event.end = ics_event.end.astimezone(tz=self.tzinfo)
            ics_event.formated = formated(ics_event)
            filtered_events.append(ics_event)

        return filtered_events


async def create_event(event: Event, calendar: Calendar):
    logger.debug(f"Calendar get event {event.value}")
    data = json.loads(event.value)
    start = data['start']
    end = data['end']
    start_date = datetime.datetime(start["year"], start["month"], start["day"], start["hour"], start["minute"])
    if end:
        end_date = datetime.datetime(end["year"], end["month"], end["day"], end["hour"], end["minute"])
    else:
        end_date = start_date
    try:
        calendar.create_event(
            value=data["text"],
            start=start_date,
            end=end_date,
        )
        await event.reply(
            value=f"""Событие "{data['text']}" на """ +
                  f"""{start["day"]}.{"0" + str(start["month"]) if start["month"] < 10 else "0"} """ +
                  f"""в {start["hour"]}:{start["minute"]} добавлено.""",
            new_purpose="add_event_complete"
        )

    except Exception as e:
        logger.error(f"Calendar add_event error: {e}", exc_info=True)


if __name__ == '__main__':
    with open("settings.json", "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    config = data["config"]

    url = config["url"]
    username = config["username"]
    password = config["password"]

    calendar = Calendar(url=url, username=username, password=password)

    events = calendar.get_events()

    for event in events:
        print(event.name)
