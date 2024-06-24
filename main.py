import asyncio

from core import Core

if __name__ == '__main__':
    core = Core()
    asyncio.run(core.run())