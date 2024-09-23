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
        "examples": ["давай поболтаем", "общение", "режим диалога", "я хочу поговорить", "включи болталку", "разговор с гпт"],
        "function": context_setter
    }
]