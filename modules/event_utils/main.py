import logging
from .utils import num_to_word, change_type


logger = logging.getLogger("root")


extensions = [
    {
        "name": "num_to_word",
        "function": num_to_word
    },
    {
        "name": "change_type",
        "function": change_type
    },
]
