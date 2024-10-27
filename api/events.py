from typing import List

from fastapi import APIRouter

from .classes import EventData, AnswerData
from .get_core import CoreDep

events = APIRouter(tags=["events"])


@events.get("")
async def get_events(core: CoreDep, count: int = 1) -> List[EventData]:
    return {"message": "Hello World"}


@events.post("")
async def post_event(core: CoreDep, event: EventData):
    return {"message": "Hello World"}


@events.post("/{id}/answer")
async def post_event(core: CoreDep, id: str, event: AnswerData):
    return {"message": "Hello World"}
