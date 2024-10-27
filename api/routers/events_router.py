from typing import List

from fastapi import APIRouter

from api.classes import EventData, AnswerData
from api.get_core import CoreDep

events_router = APIRouter(tags=["events"])


@events_router.get("")
async def get_events(core: CoreDep, count: int = 1) -> List[EventData]:
    return {"message": "Hello World"}


@events_router.post("")
async def post_event(core: CoreDep, event: EventData):
    return {"message": "Hello World"}


@events_router.post("/{id}/answer")
async def post_event(core: CoreDep, id: str, event: AnswerData):
    return {"message": "Hello World"}
