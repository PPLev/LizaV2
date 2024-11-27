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

SPK_MODEL_PATH = "/D/projects/Liza/modules/vosk/vosk-model-spk-0.4"


spk_model = vosk.SpkModel(SPK_MODEL_PATH)

vosk_model = None
spk_sig = [-1.122393, -0.199941, 0.025894, 0.604144, -0.854399, -0.751831, 0.272273, 0.180137, 1.002845, 0.887966,
           -0.408213, -0.885447, 0.572998, 0.065982, -0.225658, 1.477786, 0.228749, 1.615168, -1.770548, -0.368776,
           0.086276, -0.945274, 1.630447, 0.280204, -0.114323, 0.667123, 0.771218, -0.8222, 0.419256, 1.615388,
           0.904648, 0.075145, 1.324923, 0.284862, 0.076533, 0.031045, 0.704339, -0.183363, -0.084622, 0.492897,
           -0.814483, -0.488089, -0.43135, -0.732461, -0.64371, -1.009462, -0.771733, 0.823881, 1.431894, 0.972702,
           -0.764888, -0.239566, -1.184187, 1.145945, -0.347205, 0.798138, -1.294208, 1.641347, 0.839933, 0.609021,
           -0.802076, 0.216795, -0.698201, -0.622192, 0.676424, -0.292572, -0.484084, 0.958317, -0.658632, 0.075262,
           0.454144, 2.219094, -1.027279, 0.277622, 0.927942, -0.259407, 0.426906, -1.617425, 0.13916, 0.545902,
           -0.297114, 1.517973, 0.986764, -0.092606, 0.72324, -0.357816, 0.796907, 0.526481, -3.4353, -2.404602,
           -0.277518, 0.511036, -0.994936, -1.615596, -0.149478, 0.160914, 3.029633, 1.207272, 1.281053, 0.788055,
           -2.716715, 0.336289, -0.629901, -0.873426, 0.807854, -1.852178, 0.245839, 0.606305, 0.768468, -0.018235,
           -1.123807, -1.376217, -0.417029, 0.72571, 0.586008, 0.06681, -0.210671, -0.903194, 0.763359, 1.866145,
           -0.232697, -0.936248, -1.136488, -0.149607, 1.236572, 1.394734, 0.439408, 1.728618]


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


def download_model(model_name):
    MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
    file_name = f"modules/vosk/{model_name}.zip"

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

    model_dir_path = f"modules/vosk/{model_name}"

    if not os.path.isdir(model_dir_path):
        download_model(model_name=model_name)

    if vosk_model is None:
        vosk_model = vosk.Model(model_dir_path)  # Подгружаем модель

    if ext_only:
        return

    rec = vosk.KaldiRecognizer(vosk_model, 44100)
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
                print("X-vector:", recognized_data["spk"])
                print("Speaker distance:", cosine_dist(spk_sig, recognized_data["spk"]),
                      "based on", recognized_data["spk_frames"], "frames")

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
