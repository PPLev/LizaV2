# from .utils import init, add_event
#
# acceptors = [
#     {
#         "name": "updater_acceptor",
#         "function": updater_acceptor
#     }
# ]

# senders = [
#     {
#         "name": "vosk_send",
#         "function": run_vosk
#     }
# ]
#
# intents = [
#     {
#         "name": "check_update",
#         "examples": ["проверь обновления", "есть ли новая версия", "проверь версию"],
#         "queue": "updater_acceptor",
#         "purpose": "inspect"
#     },
#     {
#         "name": "update",
#         "examples": ["обновись", "выполни обновление", "скачай обновление"],
#         "queue": "updater_acceptor",
#         "purpose": "run_update"
#     }
# ]
#
# extensions = [
#     {
#         "name": "recognize_file_vosk",
#         "function": recognize_file_vosk
#     }
# ]