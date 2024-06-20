from dataclasses import dataclass


@dataclass
class EventTypes:
    text = "text"


class Event:
    def __init__(self, event_type: str, value=None):
        self.event_type = event_type
        self.value = value

    @staticmethod
    def from_dict(data: dict):
        event = Event(
            event_type=data["type"],
            value=data["value"]
        )
        return event

