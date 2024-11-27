import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import dotenv

from event import Event, EventTypes

router = Router()

logger = logging.getLogger("root")

bot: Bot = None
dp: Dispatcher = None


# async def send_msg(event: Event):
#     await bot.send_queue.put(
#
#     )


@router.message(F.text == "/start")
async def command_handler(msg: types.Message, bot: Bot, *args, **kwargs):
    if msg.from_user.id == bot.admin_id:
        await msg.reply("Я тут)")
    else:
        await msg.reply(
            text=bot.guest_text
        )

# Тест ивентов - запросов в ядро, прим. сообщения боту "/test get_extensions"
# @router.message(F.text.startswith("/test"))
# async def command_handler(msg: types.Message, bot: Bot, *args, **kwargs):
#     if msg.from_user.id == bot.admin_id:
# 
#         async def tester(data):
#             await msg.reply(str(data))
# 
#         await bot.send_queue.put(
#             Event(
#                 event_type=EventTypes.core_query,
#                 value=msg.text.replace("/test ", ""),
#                 callback=tester
#             )
#         )
#     else:
#         await msg.reply(
#             text=bot.guest_text
#         )


@router.message(F.text)
async def msg_handler(msg: types.Message, bot: Bot, *args, **kwargs):
    if msg.from_user.id == bot.admin_id:
        await bot.send_queue.put(
            Event(
                event_type=EventTypes.user_command,
                value=msg.text,
                purpose="tg_msg"
            )
        )
        # await msg.reply(answer)
    else:
        await msg.reply(
            text=bot.guest_text
        )


@router.message(F.voice)
async def voice_handler(msg: types.Message, bot: Bot, *args, **kwargs):
    if msg.from_user.id == bot.admin_id:
        file_id = msg.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, "last_voice.wav")

        await bot.send_queue.put(
            Event(
                event_type=EventTypes.text,
                value="last_voice.wav",
                purpose="voice",
            )
        )
        logger.debug("TG Bot: войс отправлен в очередь")
        # text = core.recognize_file("last_voice.wav")
        # await msg.reply(f"Услышала:\n{text}")
        # answer = core.run_str(text, is_name_find=True, return_answer=True)
        # await msg.reply(answer)
    else:
        await msg.reply(
            text=bot.guest_text
        )


async def msg_sender(queue: asyncio.Queue = None, **kwargs):
    global bot
    while True:
        await asyncio.sleep(0)
        if not queue.empty():
            event = await queue.get()
            await bot.send_message(
                chat_id=bot.admin_id,
                text=event.value
            )


async def run_client(queue: asyncio.Queue, config: dict):
    global bot, dp

    admin_id = config["admin_id"]
    guest_text = config["guest_text"]

    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        logger.error("Telegram bot token not set, to use telegram bot - set token as TG_BOT_TOKEN in env")
        return

    try:
        bot = Bot(token=token)
        bot.admin_id = admin_id
        bot.guest_text = guest_text
        bot.send_queue = queue
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)
    except:
        return

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def stop_client():
    global dp
    try:
        await dp.stop_polling()
    except:
        pass
