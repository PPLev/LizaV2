import asyncio
import logging
import os.path
import time
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import sounddevice
from tqdm import tqdm
from vosk_tts import Model, Synth

from event import Event, EventTypes

logger = logging.getLogger("root")

model: Model = None
synth: Synth = None
speaker_id: int = None
output_q: asyncio.Queue = None


def canceler():
    sounddevice.stop()


async def say(audio: np.ndarray, sampling_rate: int) -> None:
    global output_q
    await output_q.put(
        Event(
            event_type=EventTypes.text,
            value=audio.copy(),
            purpose="set_voice_buffer"
        )
    )

    timer = (len(audio) / sampling_rate) + time.time()

    sounddevice.play(audio, samplerate=sampling_rate)

    while time.time() < timer:
        await asyncio.sleep(0.1)

    await output_q.put(
        Event(
            event_type=EventTypes.text,
            purpose="unset_voice_buffer"
        )
    )


async def run_sender(queue: asyncio.Queue = None, config: dict = None):
    global output_q
    output_q = queue


async def gen_acceptor(queue: asyncio.Queue = None, config: dict = None):
    global synth, speaker_id
    while True:
        await asyncio.sleep(0)

        if not queue.empty():
            event: Event = await queue.get()
            try:
                audio = synth.synth_audio(
                    text=event.value,
                    speaker_id=speaker_id
                )
                await say(audio=audio, sampling_rate=24000)
            except Exception as e:
                logger.error(f"Ошибка озвучки для {event.value}", exc_info=True)


def gen_voice(event: Event):
    global synth, speaker_id

    file_name = f"modules/tts_vosk/cache/{event.value[:20]}.wav"
    synth.synth(event.value, file_name, speaker_id=speaker_id)


def download_model(model_name):
    MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
    file_name = f"modules/tts_vosk/{model_name}.zip"

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
            model_ref.extractall(f"modules/tts_vosk/")
        Path(file_name).unlink()


async def init(config: dict):
    global model, synth, speaker_id

    speaker_id = config["speaker_id"]
    if not os.path.isdir(f"modules/tts_vosk/{config['model_name']}"):
        download_model(config['model_name'])

    model = Model(model_path=f"modules/tts_vosk/{config['model_name']}")
    synth = Synth(model)
