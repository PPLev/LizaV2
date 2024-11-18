from .utils import init, cal_acceptor, cal_sender

acceptor = cal_acceptor

sender = cal_sender
#
intents = [
    {
        "name": "add_event",
        "queue": "calendar",
        "purpose": "pre_add_event"
    },
    {
        "name": "get_event",
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