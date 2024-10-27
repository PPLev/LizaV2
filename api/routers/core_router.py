import asyncio

from fastapi import APIRouter

from api.get_core import CoreDep
from api.classes import CoreData

core_router = APIRouter(tags=["core"])


@core_router.get("/status")
async def get_core_status(core: CoreDep) -> CoreData:
    return CoreData(is_running=core.is_running)


@core_router.get("/run")
async def run_core(core: CoreDep) -> CoreData:
    asyncio.run_coroutine_threadsafe(core.run(), loop=asyncio.get_event_loop())
    await core.wait_for_run()
    return CoreData(is_running=core.is_running)


# @core_router.get("/status")
# async def get_events(core: CoreDep) -> CoreData:
#     return CoreData(is_running=core.is_running)
