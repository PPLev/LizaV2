import uuid
from typing import List, Union, Any
from pydantic import BaseModel, Field

from event import Event


class AnswerData(BaseModel):
    answer_id: uuid.UUID


class EventData(BaseModel):
    id: str | None = Field(default_factory=Union[str, None], alias="id", description="Use for answer only")
    event_type: str
    value: str
    purpose: str | None = None
    from_module: str | None = None
    other_keys: dict | None = None

    @staticmethod
    def from_event(event: Event):
        data = event.to_dict()
        event_data = EventData(id="0", **data)
        return event_data


class IntentData(BaseModel):
    name: str
    examples: List[str]


class ModuleData(BaseModel):
    name: str
    version: str
    config: dict[str, Any]


class CoreData(BaseModel):
    is_running: bool
