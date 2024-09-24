from typing import List

from fastapi import APIRouter

from .classes import EventData, AnswerData

events = APIRouter(tags=["events"])


@events.get("")
async def get_events(count: int = 1) -> List[EventData]:
    return {"message": "Hello World"}


@events.post("")
async def post_event(event: EventData):
    return {"message": "Hello World"}


@events.post("/{id}/answer")
async def post_event(id: str, event: AnswerData):
    return {"message": "Hello World"}