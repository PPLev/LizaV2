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
        "examples": ["проверь есть ли обновление", "узнай есть ли новая версия", "проверь наличие новой версии", "проверь обновление"],
        "queue": "update",
        "purpose": "inspect"
    },
    {
        "name": "update",
        "examples": ["загрузи обновление", "выполни обновление системмы", "скачай свежее обновление", "обновись до последней версии"],
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
