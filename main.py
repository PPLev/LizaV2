import asyncio

from core import Core

if __name__ == '__main__':
    core = Core(connection_config_path="connections/config.yml")
    core.init()
    asyncio.run(core.run())
