import asyncio
import json
import os
import wave

import soundfile
import vosk
import pyaudio
import logging
from event import EventTypes, Event
from .audio_utils import filter_voice_gen

logger = logging.getLogger("root")

vosk_model = None
buffer = None


def file_recognizer(file):
    global vosk_model
    data, samplerate = soundfile.read(file)
    soundfile.write(file, data, samplerate)

    wf = wave.open(file, "rb")

    rec = vosk.KaldiRecognizer(vosk_model, 44100)
    rec.SetWords(True)
    rec.SetPartialWords(True)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    if "text" in (recognized := json.loads(rec.FinalResult())):
        return recognized["text"]
    return "Не распознано("


async def recognize_file_vosk(event: Event):
    file_name = event.value
    text = file_recognizer(file=file_name)
    event.value = text
    return event


async def vosk_acceptor(
        queue: asyncio.Queue = None,
        config: dict = None,
):
    global buffer
    while True:
        await asyncio.sleep(0)

        if not queue.empty():
            event: Event = await queue.get()

            if event.purpose == "set_voice_buffer":
                buffer = event.value

            if event.purpose != "unset_voice_buffer":
                buffer = None


async def run_vosk(
        queue: asyncio.Queue = None,
        config: dict = None,
):
    global vosk_model, buffer

    model_dir_path: str = config["model_dir_path"]
    input_device_id = config["input_device_id"]
    send_text_event = config["send_text_event"]
    ext_only = config["ext_only"]
    trigger_name = config["trigger_name"]

    if not os.path.isdir(model_dir_path):
        logger.warning("Vosk: Папка модели воск не найдена\n"
                       "Please download a model for your language from https://alphacephei.com/vosk/models")
        raise FileNotFoundError

    if vosk_model is None:
        vosk_model = vosk.Model(model_dir_path)  # Подгружаем модель

    if ext_only:
        return

    rec = vosk.KaldiRecognizer(vosk_model, 44100)

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=44100,
                     input=True,
                     input_device_index=input_device_id,
                     frames_per_buffer=8000)

    names = []
    if trigger_name:
        names = [i for i in trigger_name.split("|")]

    logger.info("Запуск распознователя речи vosk вход в цикл")

    while True:
        await asyncio.sleep(0)

        data = stream.read(8000)
        data = filter_voice_gen(data, buffer)
        if rec.AcceptWaveform(data):
            recognized_data = rec.Result()
            recognized_data = json.loads(recognized_data)
            voice_input_str: str = recognized_data["text"]
            if voice_input_str != "" and voice_input_str is not None:
                logger.info(f"Распознано Vosk: '{voice_input_str}'")
                if len(names):
                    for name in names:
                        if name not in voice_input_str:
                            continue

                        logger.debug("Имя обнаружено!")
                        voice_input_str = " ".join(voice_input_str.split(name)[1:])
                        voice_input_str = voice_input_str.strip()
                        break

                    else:
                        logger.debug("Имя не найдено!")
                        continue

                await queue.put(
                    Event(
                        event_type=EventTypes.user_command,
                        value=voice_input_str
                    )
                )
                if send_text_event:
                    await queue.put(
                        Event(
                            event_type=EventTypes.text,
                            value=voice_input_str
                        )
                    )

                logger.info(f"Vosk - передано в очередь: '{voice_input_str}'")
