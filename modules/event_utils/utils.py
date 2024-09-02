from num2words import num2words

from event import Event, EventTypes


def num_to_word(event: Event):
    raw_text = event.value
    text = ""
    for i in raw_text.split(" "):
        text += " " + num2words(int(i), lang='ru') if i.isdigit() else i
    event.value = text

    return event


def change_type(event: Event, new_type: str = EventTypes.text):
    event.type = new_type
    return event


def change_purpose(event: Event, new_purpose: str = "none"):
    event.purpose = new_purpose
    return event

# def move_queue(event: Event):