import asyncio
import logging
import os
import time

import sounddevice
import torch
from event import EventTypes, Event

logger = logging.getLogger(__name__)

silero_model = None
is_mute = False
model_settings = {}
output_device_id = None

audio_queue = asyncio.Queue()

sound_playing = True


async def say_silero(model_path: str,
                     model_name: str,
                     model_url: str,
                     output_device_id=18,
                     queue: asyncio.Queue = None,
                     **kwargs):

    logger.debug("Загрузка модели силеро")
    # Если нет файла модели - скачиваем
    if not os.path.isfile(model_path + model_name):
        logger.debug("Скачивание модели silero")
        torch.hub.download_url_to_file(
            model_url, model_path + model_name
        )

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

            # event.value

            say_str = event.value.replace("…", "...")

            logger.info(f"Генерация аудио для '{say_str}'")
            audio = silero_model.apply_tts(text=say_str,
                                           speaker="xenia",
                                           sample_rate=24000)

            if output_device_id:
                sounddevice.default.device = (None, output_device_id)

            # sound_playing = True
            # logger.info(f"Статус записи: {sound_playing}")
            sounddevice.play(audio, samplerate=24000)
            sounddevice.wait()
            # sound_playing = False
            # logger.info(f"Статус записи: {sound_playing}")
            logger.info(f"Озвучка завершена {say_str}")

    # if is_mute:
    #     return




    # if not output_str:
    #     return
    #
    # say_str = "Привет хозяин"

    # sounddevice.play(audio, samplerate=24000)
    # TODO: Сделать блокировку распознавания при воспроизведении
    # sounddevice.wait()




# @core.on_output.register()
# async def say_silero(package: packages.TextPackage):
#     await _say_silero(core, package.input_text)
#     if package.text:
#         await _say_silero(core, package.text)
#
#
# @core.on_input.register(levenshtein_filter("без звука", min_ratio=85))
# async def mute(package):
#     global is_mute
#     is_mute = not is_mute
