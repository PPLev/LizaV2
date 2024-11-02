import asyncio

from core import Core

if __name__ == '__main__':
    core = Core(connection_config_path="connections/config.yml", forward_core_events=True)
    core.init()
    asyncio.run(core.run())
