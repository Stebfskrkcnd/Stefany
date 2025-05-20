from config import USUARIOS_AUTORIZADOS, BOT_TOKEN
from telegram import Bot

async def notificar_admins(mensaje):
    bot = Bot(token=BOT_TOKEN)
    for uid in USUARIOS_AUTORIZADOS:
        try:
            await bot.send_message(chat_id=uid, text=mensaje)
        except:
            pass