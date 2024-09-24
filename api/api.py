from typing import List

from fastapi import FastAPI, APIRouter

from .events import events
from .intents import intents

app = FastAPI(
    title="Liza-API",
    description="Интерфейс взаимодействия через интернет",
)


app.include_router(prefix="/events", router=events)
app.include_router(prefix="/intents", router=intents)

