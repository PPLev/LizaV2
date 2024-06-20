import recognizer

acceptors = []

senders = [
    {
        "name": "vosk_send"
    }
]

workers = [
    recognizer.run_vosk
]