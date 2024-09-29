import asyncio
import os.path

import sounddevice
from vosk_tts import Model, Synth

from event import Event

model: Model = None
synth: Synth = None
speaker_id: int = None

# model = Model(model_name="vosk-model-tts-ru-0.7-multi")
# synth = Synth(model)


async def say_acceptor(queue: asyncio.Queue = None, config: dict = None):
    global synth, speaker_id
    while True:
        while True:
            await asyncio.sleep(0)

            if not queue.empty():
                event: Event = await queue.get()
                audio = synth.synth_audio(
                    text=event.value,
                    speaker_id=speaker_id
                )

                sounddevice.play(audio, samplerate=24000)
                sounddevice.wait()


def gen_voice(event: Event):
    global synth, speaker_id

    file_name = f"modules/vosk_tts/cache/{event.value[:20]}.wav"
    synth.synth(event.value, file_name, speaker_id=speaker_id)
    

async def init(config: dict):
    global model, synth, speaker_id

    speaker_id = config["speaker_id"]
    model = Model(model_name=config["model_name"])
    synth = Synth(model)
    