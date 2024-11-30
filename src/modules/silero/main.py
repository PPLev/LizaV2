from .utils import say_acceptor, canceler

acceptor = say_acceptor


intents = [
    {
        "name": "stop_gen_voice_silero",
        "function": canceler
    }
]

sender = None
