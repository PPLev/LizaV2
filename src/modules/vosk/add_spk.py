import json
import os.path

from event import Event


async def saver(event: Event, *args, **kwargs):
    if event.from_module != "vosk":
        await event.reply("Запись голоса возможна только через модуль воска.")
        return

    if event.value != "cиняя цапля сидит в доме у мачты":
        await event.reply("Ошибка, попробуйте еще раз.")
        return

    if not os.path.isdir("modules/vosk/spk_data"):
        os.mkdir("modules/vosk/spk_data")
    sig_number = len(os.listdir('modules/vosk/spk_data')) + 1

    with open(f"modules/vosk/spk_data/user_{sig_number}.json", "w", encoding="utf-8") as file:
        json.dump({"spk_sig": event.spk}, file)

    if sig_number % 3 == 0:
        await event.reply("Голос добавлен!")
        await event.end_context()
    else:
        await event.reply("Продолжай")


async def run_add_spk(event: Event):
    if event.from_module != "vosk":
        await event.reply("Запись голоса возможна только через модуль воска.")
        return

    await event.reply("Для добавления образца голоса тебе надо три раза произнести следующую фразу. "
                      "Синяя цапля сидит в доме у мачты. Можешь начинать.")

    await event.set_context(callback=saver)

