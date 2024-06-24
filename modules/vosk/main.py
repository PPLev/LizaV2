from .recognizer import run_vosk

acceptors = []

senders = [
    {
        "name": "vosk_send",
        "function": run_vosk
    }
]

intents = []