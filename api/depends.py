import asyncio
import uuid
import time
from typing import Annotated, List

from fastapi import Depends

from core import Core
from event import Event

core = Core()
core.init()


class AnswerQueue:
    def __init__(self, timeout=60):
        self.id = uuid.uuid4()
        self.timestamp = time.time() + timeout
        self.queue = asyncio.Queue()


class AnswerQueues:
    def __init__(self):
        self.queues: List[AnswerQueue] = []

    def new(self) -> AnswerQueue:
        self.queues.append(AnswerQueue())
        return self.queues[-1]

    async def get_events(self, id: uuid.uuid4, count=1) -> List[Event]:
        for answer_queue in self.queues:
            if answer_queue.id == id:
                if answer_queue.timestamp < time.time():
                    self.queues.remove(answer_queue)
                    return None

                events = []
                for _ in range(count):
                    if answer_queue.queue.empty():
                        continue
                    event = await answer_queue.queue.get()
                    events.append(event)
                return events

        return None


http_queues = AnswerQueues()


def get_core() -> Core:
    yield core


CoreDep = Annotated[Core, Depends(get_core)]


def get_queue_mng() -> AnswerQueue:
    yield http_queues


HttpQueuesDep = Annotated[AnswerQueues, Depends(get_queue_mng)]
