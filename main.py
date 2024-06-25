import asyncio

from core import Core

if __name__ == '__main__':
    core = Core()
    core.init()
    asyncio.run(core.run())