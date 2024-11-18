import uuid
from typing import List

from fastapi import APIRouter, Response

from api.classes import EventData, AnswerData
from api.depends import CoreDep, HttpQueuesDep
from event import Event

events_router = APIRouter(tags=["events"])


# @events_router.get("")
# async def get_events(queue: HttpQueueDep, count: int = 1) -> List[EventData]:
#     events = []
#     for i in range(count):
#         if queue.empty():
#             continue
#         event = await queue.get()
#         events.append(EventData.from_event(event=event))
#     return events


@events_router.post("")
async def post_event(core: CoreDep, queues_mng: HttpQueuesDep, event: EventData, timeout: int = 60) -> AnswerData:
    event_ = Event.from_dict(event.model_dump())
    answer_queue = queues_mng.new(timeout=timeout)
    event_.out_queue = answer_queue.queue
    await core.run_event(event_)

    return AnswerData(answer_id=answer_queue.id)


# @events_router.post("/{id}/answer")
# async def post_event(core: CoreDep, id: uuid.uuid4, event: AnswerData):
#     return {"message": "Hello World"}


@events_router.get("/{queue_id}/answer")
async def post_event(queues_mng: HttpQueuesDep, queue_id: uuid.UUID, count: int = 1) -> List[EventData]:
    answer_events = await queues_mng.get_events(id=queue_id, count=count)
    if answer_events is None:
        return Response(status_code=404)

    return [EventData.from_event(event) for event in answer_events]
