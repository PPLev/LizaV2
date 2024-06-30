from .recognizer import run_vosk, file_acceptor

acceptors = [
    {
        "name": "vosk_acceptor",
        "function": file_acceptor
    }
]

senders = [
    {
        "name": "vosk_send",
        "function": run_vosk
    }
]

intents = []