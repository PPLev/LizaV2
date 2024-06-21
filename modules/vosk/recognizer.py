import asyncio
import json
import os
import sys

# import soundfile
# import sounddevice
import vosk
import pyaudio
import logging
from event import EventTypes, Event

logger = logging.getLogger("root")


# def recognize_file(file):
#     data, samplerate = soundfile.read(file)
#     soundfile.write(file, data, samplerate)
#
#     wf = wave.open(file, "rb")
#
#     if vosk_model is None:
#         load_model()
#     rec = vosk.KaldiRecognizer(vosk_model, 44100)
#     rec.SetWords(True)
#     rec.SetPartialWords(True)
#
#     while True:
#         data = wf.readframes(4000)
#         if len(data) == 0:
#             break
#         rec.AcceptWaveform(data)
#
#     if "text" in (recognized := json.loads(rec.FinalResult())):
#         return recognized["text"]
#     return "Не распознано("


async def run_vosk(model_dir_path: str, input_device_id=-1, queue: asyncio.Queue = None, **kwargs):
    """
    Распознование библиотекой воск
    """

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=44100,
                     input=True,
                     input_device_index=input_device_id,
                     frames_per_buffer=8000)

    if not os.path.isdir(model_dir_path):
        logger.warning("Папка модели воск не найдена\n"
                       "Please download a model for your language from https://alphacephei.com/vosk/models")
        sys.exit(0)

    vosk_model = vosk.Model(model_dir_path)  # Подгружаем модель
    rec = vosk.KaldiRecognizer(vosk_model, 44100)

    logger.info("Запуск распознователя речи vosk вход в цикл")

    while True:
        await asyncio.sleep(0)

        data = stream.read(8000)
        if rec.AcceptWaveform(data):
            recognized_data = rec.Result()
            recognized_data = json.loads(recognized_data)
            voice_input_str = recognized_data["text"]
            if voice_input_str != "" and voice_input_str is not None:
                logger.info(f"Распознано Vosk: '{voice_input_str}'")
                await queue.put(
                    Event(
                        event_type=EventTypes.user_command,
                        value=voice_input_str
                    )
                )
