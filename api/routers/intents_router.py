from typing import List

from fastapi import APIRouter

from api.classes import IntentData
from api.get_core import CoreDep

intents_router = APIRouter(tags=["intents"])


@intents_router.get("")
async def get_intents(core: CoreDep) -> List[IntentData]:
    data = [
        IntentData(name=name, examples=examples)
        for name, examples in core.nlu.intents.items()
    ]
    return data
