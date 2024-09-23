from typing import List, Union

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


events = APIRouter(tags=["events"])

app = FastAPI(
    title="Liza-API",
    description="Интерфейс взаимодействия через интернет",
)


@events.get("")
async def get_events(count: int = 1) -> List[EventData]:
    return {"message": "Hello World"}


@events.post("")
async def post_event(event: EventData):
    return {"message": "Hello World"}


@events.post("/{id}/answer")
async def post_event(id: str, event: AnswerData):
    return {"message": "Hello World"}


app.include_router(prefix="/events", router=events)

