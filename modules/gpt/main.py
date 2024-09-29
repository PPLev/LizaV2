from .utils import ask_gpt, init, context_setter

extensions = [
    {
        "name": "ask_gpt",
        "function": ask_gpt
    }
]

intents = [
    {
        "name": "gpt_dialog",
        "function": context_setter
    }
]