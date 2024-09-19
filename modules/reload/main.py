import os
import sys
import logging

from event import Event

logger = logging.getLogger("root")


async def reload(event: Event):  # полный перезапуск
    logger.debug(f"Reload...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


intents = [
    {
        "name": "reload",
        "examples": ["перезагрузка", "перезагрузись", "выполни перезагрузку", "рестарт"],
        "function": reload
    }
]
