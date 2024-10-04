import calendar
import json
from dataclasses import dataclass
import datetime
import logging
from typing import List

import caldav
#import icalendar
import icalendar
#import vobject
from event import Event

logger = logging.getLogger(__name__)


@dataclass
class CalendarData:
    url: str
    username: str
    password: str


class CalEvent:
    def __init__(self, event: icalendar.Event):
        self._event = event

    @staticmethod
    def from_caldav_event(event: caldav.Event):
        cal = icalendar.Event.from_ical(event.data)
        return CalEvent(cal)

    def get_component(self):
        for component in self._event.subcomponents:
            if "SUMMARY" in component:
                return component

    @property
    def summary(self) -> str:
        return self.get_component()["SUMMARY"].to_ical().decode()

    @summary.setter
    def summary(self, value: str):
        self.get_component()["SUMMARY"] = icalendar.vText(value)

    @property
    def dtstart(self) -> datetime.datetime:
        return self.get_component()["DTSTART"].dt

    @dtstart.setter
    def dtstart(self, value: datetime.datetime):
        self.get_component()["DTSTART"] = value

    @property
    def dtend(self) -> datetime.datetime:
        return self.get_component()["DTEND"].dt

    @dtend.setter
    def dtend(self, value: datetime.datetime):
        self.get_component()["DTEND"] = value


class Calendar:
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

    def get_events(
            self,
            start: datetime = datetime.datetime.now(),
            end: datetime = datetime.datetime.now() + datetime.timedelta(days=1)
    ) -> List[CalEvent]:
        pass
        events = self._calendar.events()
        events = [CalEvent.from_caldav_event(event) for event in events]

        filtered_events = []

        for event in events:
            if start <= event.dtstart < end or \
                    start < event.dtend <= end or \
                    start <= event.dtstart and event.dtend <= end:
                filtered_events.append(event)

        return filtered_events


async def create_event(event: Event, calendar: caldav.Calendar):
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


if __name__ == '__main__':
    with open("settings.json", "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    config = data["config"]

    url = config["url"]
    username = config["username"]
    password = config["password"]

    client = caldav.DAVClient(url=url, username=username, password=password)
    calendar = client.calendar(url=url)

    events = calendar.events()

    for event in events:
        my_event = CalEvent.from_caldav_event(event)
        print(my_event.summary)