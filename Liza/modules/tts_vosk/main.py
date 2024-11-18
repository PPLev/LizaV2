from .gen import init, gen_acceptor, gen_voice, canceler, run_sender


acceptor = gen_acceptor
#
sender = run_sender
#
intents = [
    {
        "name": "stop_gen_voice_vosk",
        "function": canceler
    }
]
#
extensions = [
    {
        "name": "gen_voice_vosk",
        "function": gen_voice
    }
]
