from .utils import run_client
acceptors = []

senders = [
    {
        "name": "telegram_bot_sender",
        "function": run_client
    }
]

intents = []