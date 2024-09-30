from datetime import datetime, timedelta

import peewee

from event import Event

DATABASE = "modules/remind/remind.db"

database = peewee.SqliteDatabase(DATABASE)


class BaseModel(peewee.Model):
    class Meta:
        database = database


class Note(BaseModel):
    title = peewee.CharField()
    text = peewee.CharField()
    remind_date = peewee.DateTimeField()
    create_date = peewee.DateTimeField()
    target_date = peewee.DateTimeField()

    @staticmethod
    def create_note(title, text, remind_date, target_date):
        note = Note(
            title=title,
            text=text,
            remind_date=remind_date,
            target_date=target_date,
            create_date=datetime.now()
        )
        note.save()
        return note

    @staticmethod
    async def from_event(event: Event):
        # TODO: Достаем параметры из json в event.value и создаем запись
        pass


def get_notes(delta=timedelta(days=1)):
    end_time = datetime.now() + delta
    notes = Note.select().where(Note.remind_date <= end_time)
    return notes
