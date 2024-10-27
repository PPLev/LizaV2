from typing import List

from fastapi import APIRouter

from .classes import IntentData
from .get_core import CoreDep

intents = APIRouter(tags=["intents"])


@intents.get("")
async def get_intents(core: CoreDep) -> List[IntentData]:
    data = [
        IntentData(name=name, examples=examples)
        for name, examples in core.nlu.intents.items()
    ]
    return data
