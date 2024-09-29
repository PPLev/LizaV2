import asyncio
from dataclasses import dataclass


@dataclass
class EventTypes:
    text = "text"
    user_command = "user_command"


class Event:
    def __init__(self, event_type: str, value=None, purpose=None, out_queue: asyncio.Queue = None, from_module: str = None, **kwargs):
        self.event_type = event_type
        self.value = value
        self.purpose = purpose
        self.out_queue = out_queue
        self.from_module = from_module
        self.context = None
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

    async def reply(self, value, new_purpose=None):
        if self.out_queue:
            await self.out_queue.put(
                Event(
                    event_type=EventTypes.text,
                    value=value,
                    purpose=new_purpose,
                )
            )

    def copy(self):
        return Event.from_dict(self.__dict__.copy())

    # @property
    # def context(self):
    #     raise Exception("Context is not defined, see: https://github.com/AzimovIz/Liza/blob/dev/docs/docs/Контекст.md")

    async def set_context(self, callback: callable, init_context_data: dict):
        # See Core.preconfigure_context()
        pass

    async def end_context(self):
        # See Core.del_context()
        pass


if __name__ == '__main__':
    event = Event.from_dict({"event_type": "user_command", "value": 1})
    print(event)
    event2 = event.copy()
    print(event2)