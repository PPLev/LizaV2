from .utils import updater_acceptor

acceptor = updater_acceptor

# senders = [
#     {
#         "name": "vosk_send",
#         "function": run_vosk
#     }
# ]

intents = [
    {
        "name": "check_update",
        "queue": "update",
        "purpose": "inspect"
    },
    {
        "name": "update",
        "queue": "update",
        "purpose": "update"
    }
]
#
# extensions = [
#     {
#         "name": "recognize_file_vosk",
#         "function": recognize_file_vosk
#     }
# ]
