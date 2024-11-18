from .recognizer import run_vosk, recognize_file_vosk, vosk_acceptor

acceptor = vosk_acceptor

sender = run_vosk

intents = []

extensions = [
    {
        "name": "recognize_file_vosk",
        "function": recognize_file_vosk
    }
]
