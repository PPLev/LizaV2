import logging
from .utils import num_to_word, change_type, change_purpose, json_find, set_value

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
    {
        "name": "change_purpose",
        "function": change_purpose
    },
    {
        "name": "set_value",
        "function": set_value
    },
    {
        "name": "json_find",
        "function": json_find
    },
]
