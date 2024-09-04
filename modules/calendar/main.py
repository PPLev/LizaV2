from .utils import init, add_event

acceptors = [
    {
        "name": "calendar_acceptor",
        "function": add_event
    }
]

# senders = [
#     {
#         "name": "vosk_send",
#         "function": run_vosk
#     }
# ]
#
# intents = []
#
# extensions = [
#     {
#         "name": "recognize_file_vosk",
#         "function": recognize_file_vosk
#     }
# ]