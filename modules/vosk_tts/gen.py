from vosk_tts import Model, Synth

from event import Event

model = Model(model_name="vosk-model-tts-ru-0.7-multi")
synth = Synth(model)


def gen_voice(event: Event):
    if
    synth.synth("Привет мир!", f"modules/vosk_tts/{event.value[:20]}.wav", speaker_id=2)