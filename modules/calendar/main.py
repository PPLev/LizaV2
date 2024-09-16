from .utils import init, cal_acceptor, cal_sender

acceptor = cal_acceptor

sender = cal_sender
#
intents = [
    {
        "name": "add_event",
        "examples": ["запомни какое-то событие", "запиши что мне надо", "добавь событие о чем-то", "напомни мне об этом позже", "напомни через час полить цветы"],
        "queue": "calendar",
        "purpose": "pre_add_event"
    },
    {
        "name": "get_event",
        "examples": ["напомни когда произойдет это", "скажи когда произойдет что-то", "через сколько дней будет это"],
        "queue": "calendar",
        "purpose": "pre_get_event"
    }
]
#
# extensions = [
#     {
#         "name": "recognize_file_vosk",
#         "function": recognize_file_vosk
#     }
# ]