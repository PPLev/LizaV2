import logging

from .utils import precreate

logger = logging.getLogger(__name__)

# acceptor = remind_acceptor
# sender = remind_sender

intents = [
    {
        "name": "create_remind",
        "function": precreate
    }
]
