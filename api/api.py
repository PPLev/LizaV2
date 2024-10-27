from fastapi import FastAPI

from .events import events
from .intents import intents

app = FastAPI(
    title="Liza-API",
    description="HTTP-API Интерфейс взаимодействия",
)


app.include_router(prefix="/events", router=events)
app.include_router(prefix="/intents", router=intents)

