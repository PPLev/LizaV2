from fastapi import FastAPI
from .routers import core_router, events_router, modules_router, intents_router

app = FastAPI(
    title="Liza-API",
    description="HTTP-API Интерфейс взаимодействия",
)


app.include_router(prefix="/core", router=core_router)
app.include_router(prefix="/modules", router=modules_router)
app.include_router(prefix="/events", router=events_router)
app.include_router(prefix="/intents", router=intents_router)

