import asyncio
import json
import os
import wave
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import soundfile
import vosk
import pyaudio
import logging

from tqdm import tqdm

from event import EventTypes, Event
from .audio_utils import filter_voice_gen

logger = logging.getLogger("root")

vosk_model = None

def cosine_dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)


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
                logger.debug("vosk voice buffer set!!!")

            if event.purpose == "unset_voice_buffer":
                buffer = None
                logger.debug("vosk voice buffer unset!!!")


def download_model_if_not_exited(model_name):
    MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
    file_name = f"modules/vosk/{model_name}.zip"

    if os.path.isdir(file_name):
        return

    def download_progress_hook(t):
        last_b = [0]

        def update_to(b=1, bsize=1, tsize=None):
            if tsize not in (None, -1):
                t.total = tsize
            displayed = t.update((b - last_b[0]) * bsize)
            last_b[0] = b
            return displayed

        return update_to

    with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1, desc=(model_name + ".zip")) as t:
        reporthook = download_progress_hook(t)
        urlretrieve(
            MODEL_PRE_URL + model_name + ".zip", file_name,
            reporthook=reporthook,
            data=None
        )
        t.total = t.n
        with ZipFile(file_name, "r") as model_ref:
            model_ref.extractall(f"modules/vosk/")
        Path(file_name).unlink()


def load_spk_sig():
    if not os.path.isdir("modules/vosk/spk_data"):
        logger.error("vosk: нет папки сигнатур, распознование не запущено")
        raise Exception

    spks = []

    for file in os.listdir("modules/vosk/spk_data"):
        with open(os.path.join("modules/vosk/spk_data", file), "rb") as f:
            data = json.load(f)
            spks.append(data["spk_sig"])

    return spks


def check_spk(spks, data):
    for spk in spks:
        print("X-vector:", data)
        print("Speaker distance:", cosine_dist(spk, data))
        if cosine_dist(spk, data) < 0.68:
            return True
    return False


async def run_vosk(
        queue: asyncio.Queue = None,
        config: dict = None,
):
    global vosk_model, buffer

    model_name: str = config["model_name"]
    input_device_id = config["input_device_id"]
    send_text_event = config["send_text_event"]
    ext_only = config["ext_only"]
    trigger_name = config["trigger_name"]
    filter_spk = config["filter_spk"]
    spk_model = config["spk_model"]

    if filter_spk:
        allowed_spks = load_spk_sig()


    model_dir_path = f"modules/vosk/{model_name}"

    download_model_if_not_exited(model_name=model_name)
    download_model_if_not_exited(model_name=spk_model)

    if vosk_model is None:
        vosk_model = vosk.Model(model_dir_path)  # Подгружаем модель

    if ext_only:
        return

    rec = vosk.KaldiRecognizer(vosk_model, 44100)

    if filter_spk:
        spk_model = vosk.SpkModel(f"modules/vosk/{spk_model}")
        rec.SetSpkModel(spk_model)

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

        # TODO: Доработать фильтрацию, работает неправильно
        # if buffer is not None:
        #     data: np.ndarray = filter_voice_gen(np.frombuffer(data, dtype=np.int16), buffer)
        #     data: bytes = data.tobytes()

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

                if filter_spk and not ("spk" in recognized_data and check_spk(allowed_spks, recognized_data["spk"])):
                    await queue.put(
                        Event(
                            event_type=EventTypes.text,
                            value=voice_input_str,
                            purpose="spk_unverified"
                        )
                    )
                    continue

                await queue.put(
                    Event(
                        event_type=EventTypes.user_command,
                        value=voice_input_str,
                        spk=recognized_data["spk"]
                    )
                )
                if send_text_event:
                    await queue.put(
                        Event(
                            event_type=EventTypes.text,
                            value=voice_input_str,
                            spk=recognized_data["spk"]
                        )
                    )

                logger.info(f"Vosk - передано в очередь: '{voice_input_str}'")
