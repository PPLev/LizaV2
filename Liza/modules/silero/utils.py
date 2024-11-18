import asyncio
import logging
import os

import sounddevice
import torch
from event import Event

logger = logging.getLogger(__name__)


def to_waw(event: Event):
    pass


def canceler():
    sounddevice.stop()


async def say(audio):
    sounddevice.play(audio, samplerate=24000)
    while sounddevice.get_status() == "play()":
        await asyncio.sleep(0)


async def say_acceptor(
        queue: asyncio.Queue = None,
        config: dict = None,
):
    output_device_id = config['output_device_id']
    model_path = config['model_path']
    model_name = config['model_name']
    model_url = config['model_url']
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
            await say(audio=audio)
            logger.info(f"Озвучка завершена для '{say_str}'")
