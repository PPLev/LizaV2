from typing import List

from fastapi import APIRouter

from .classes import IntentData

intents = APIRouter(tags=["intents"])


@intents.get("")
async def get_intents(count: int = 1) -> List[IntentData]:
    return {"message": "Hello World"}
