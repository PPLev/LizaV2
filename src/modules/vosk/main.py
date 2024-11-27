from .add_spk import run_add_spk
from .recognizer import run_vosk, recognize_file_vosk, vosk_acceptor

acceptor = vosk_acceptor

sender = run_vosk

intents = [
    {
        "name": "add_spk",
        "function": run_add_spk
    }
]

extensions = [
    {
        "name": "recognize_file_vosk",
        "function": recognize_file_vosk
    }
]
