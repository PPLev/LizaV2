from .utils import init, cal_acceptor, cal_sender

acceptors = [
    {
        "name": "calendar_acceptor",
        "function": cal_acceptor
    }
]

senders = [
    {
        "name": "calendar_sender",
        "function": cal_sender
    }
]
#
intents = [
    {
        "name": "add_event",
        "examples": ["запомни", "запиши", "добавь событие"],
        "queue": "calendar_acceptor",
        "purpose": "pre_add_event"
    }
]
#
# extensions = [
#     {
#         "name": "recognize_file_vosk",
#         "function": recognize_file_vosk
#     }
# ]