from .utils import run_client, msg_sender

acceptors = [
    {
        "name": "telegram_bot_acceptor",
        "function": msg_sender
    }
]

senders = [
    {
        "name": "telegram_bot_sender",
        "function": run_client
    }
]

intents = [
    # {
    #     "name": "reload",
    #     "examples": ["отправь сообщение", "напиши сообщение"],
    #     "function": send_msg
    # }
]