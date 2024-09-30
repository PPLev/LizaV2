from .gen import init, say_acceptor, gen_voice


acceptor = say_acceptor
#
# sender = run_vosk
#
# intents = []
#
extensions = [
    {
        "name": "gen_voice_vosk",
        "function": gen_voice
    }
]
