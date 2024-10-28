from typing import List

from fastapi import APIRouter, Response

from api.classes import ModuleData
from api.get_core import CoreDep

modules_router = APIRouter(tags=["module"])


@modules_router.get("")
async def get_modules(core: CoreDep) -> List[ModuleData]:
    data = [
        ModuleData(name=name, version=module.version, config=module.settings.config)
        for name, module in core.MM.modules.items()
    ]
    return data


@modules_router.put("/{name}")
async def put_module(core: CoreDep, name: str, data: ModuleData):
    module = core.MM.modules[name]
    module.settings.config.update(data.config)
    module.save_settings()
    return Response(status_code=200)


@modules_router.get("/{name}/stop")
async def stop_module(core: CoreDep, name: str):
    module = core.MM.modules[name]
    await module.stop()
    return Response(status_code=200)
