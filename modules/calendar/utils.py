import os
from datetime import datetime

import caldav


def add_event():
    pass

def get_events():
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