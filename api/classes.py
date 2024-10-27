from typing import List, Union, Any

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field


class AnswerData(BaseModel):
    value: str


class EventData(BaseModel):
    id: str | None = Field(default_factory=Union[str, None], alias="id", description="Use for answer only")
    event_type: str
    value: str
    purpose: str | None = None
    from_module: str
    other_keys: dict | None = None


class IntentData(BaseModel):
    name: str
    examples: List[str]


class ModuleData(BaseModel):
    name: str
    version: str
    config: dict[str, Any]

class CoreData(BaseModel):
    is_running: bool

