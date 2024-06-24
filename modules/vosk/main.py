import recognizer

acceptors = []

senders = [
    {
        "name": "vosk_send",
        "func": recognizer.run_vosk
    }
]

intents = []