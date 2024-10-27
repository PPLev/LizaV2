from typing import Annotated

from fastapi import Depends

from core import Core

core = Core()
core.init()


def get_core() -> Core:
    yield core


CoreDep = Annotated[Core, Depends(get_core)]
