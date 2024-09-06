import asyncio
import logging
import os

import sounddevice
import torch
from event import Event

logger = logging.getLogger(__name__)


def to_waw(event: Event):
    pass


async def say_acceptor(
        model_path: str,
        model_name: str,
        model_url: str,
        output_device_id: int = None,
        queue: asyncio.Queue = None,
        **kwargs
):
    if output_device_id:
        sounddevice.default.device = (None, output_device_id)
    # Если нет файла модели - скачиваем
    if not os.path.isfile(model_path + model_name):
        logger.debug("Скачивание модели silero")
        torch.hub.download_url_to_file(
            model_url, model_path + model_name
        )

    logger.debug("Загрузка модели силеро")
    silero_model = torch.package.PackageImporter(
        model_path + model_name
    ).load_pickle("tts_models", "model")
    device = torch.device("cpu")
    silero_model.to(device)
    logger.debug("Загрузка модели силеро завершена")

    while True:
        await asyncio.sleep(0)

        if not queue.empty():
            event: Event = await queue.get()
            say_str = event.value.replace("…", "...")
            logger.info(f"Генерация аудио для '{say_str}'")
            audio = silero_model.apply_tts(text=say_str,
                                           speaker="xenia",
                                           sample_rate=24000)

            logger.info(f"Начата озвучка для '{say_str}'")
            sounddevice.play(audio, samplerate=24000)
            sounddevice.wait()
            logger.info(f"Озвучка завершена для '{say_str}'")
