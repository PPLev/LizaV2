import asyncio
import os
from core import Core
from dotenv import load_dotenv

if not os.path.isfile(".env"):
    """
    копирует переменные среды если их нет
    """
    if os.path.isfile(".env.example"):
        with open(".env.example", "r", encoding="utf-8") as f:
            env_data = f.read()

        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_data)


load_dotenv(".env")


if __name__ == '__main__':
    core = Core(connection_config_path="connections/config.yml")
    core.init()
    asyncio.run(core.run())
