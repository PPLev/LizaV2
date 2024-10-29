from typing import List

from fastapi import APIRouter

from api.classes import EventData, AnswerData
from api.get_core import CoreDep, HttpQueueDep
from event import Event

events_router = APIRouter(tags=["events"])


@events_router.get("")
async def get_events(queue: HttpQueueDep, count: int = 1) -> List[EventData]:
    events = []
    for i in range(count):
        if queue.empty():
            continue
        event = await queue.get()
        events.append(EventData.from_event(event=event))
    return events


@events_router.post("")
async def post_event(core: CoreDep, queue: HttpQueueDep, event: EventData):
    event_ = Event.from_dict(event.model_dump())
    event_.out_queue = queue
    await core.run_event(event_)
    return

@events_router.post("/{id}/answer")
async def post_event(core: CoreDep, id: str, event: AnswerData):
    return {"message": "Hello World"}


@events_router.get("/{id}/answer")
async def post_event(queue: HttpQueueDep, id: str):
    event_ = None
    return {"message": "Hello World"}
