import asyncio
import os
import shutil

from core import Core
from dotenv import load_dotenv

if not os.path.isfile(".env") and os.path.isfile(".env.example"):
    """
    копирует переменные среды если их нет
    """
    shutil.copyfile(
        src=".env.example",
        dst=".env"
    )

if os.path.isfile(".env"):
    load_dotenv(".env")


if __name__ == '__main__':
    core = Core(connection_config_path="connections/config.yml")
    core.init()
    asyncio.run(core.run())
