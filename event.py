from dataclasses import dataclass


@dataclass
class EventTypes:
    text = "text"
    user_command = "user_command"


class Event:
    def __init__(self, event_type: str, value=None, **kwargs):
        self.event_type = event_type
        self.value = value
        for key, val in kwargs.items():
            setattr(self, key, val)

    @staticmethod
    def from_dict(data: dict):
        event_type = data.pop("event_type")
        value = data.pop("value")
        event = Event(
            event_type=event_type,
            value=value,
            **data
        )
        return event
