from .recognizer import run_vosk, recognize_file_vosk

acceptors = []

senders = [
    {
        "name": "vosk_send",
        "function": run_vosk
    }
]

intents = []

extensions = [
    {
        "name": "recognize_file_vosk",
        "function": recognize_file_vosk
    }
]