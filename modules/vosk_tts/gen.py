import os.path

from vosk_tts import Model, Synth

from event import Event

model = Model(model_name="vosk-model-tts-ru-0.7-multi")
synth = Synth(model)


def gen_voice(event: Event):
    file_name = f"modules/vosk_tts/{event.value[:20]}.wav"
    if not os.path.isfile(file_name):
        synth.synth(event.value, file_name, speaker_id=2)

    # play_file(file_name)