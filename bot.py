import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)
from config import BOT_TOKEN
from handlers.commands import (
    start, estado_bot, agregar_canal, eliminar_canal,
    publicar_botonera, eliminar_botonera, autorizar,
    revocar, listar_autorizados, editar_encabezado, ver_encabezado
)
from handlers.callbacks import callback_handler

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado_bot))
    app.add_handler(CommandHandler("agregar", agregar_canal))
    app.add_handler(CommandHandler("eliminar", eliminar_canal))
    app.add_handler(CommandHandler("publicar", publicar_botonera))
    app.add_handler(CommandHandler("borrar", eliminar_botonera))
    app.add_handler(CommandHandler("autorizar", autorizar))
    app.add_handler(CommandHandler("revocar", revocar))
    app.add_handler(CommandHandler("listar", listar_autorizados))
    app.add_handler(CommandHandler("encabezado", ver_encabezado))
    app.add_handler(CommandHandler("editar_encabezado", editar_encabezado))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("✅ Bot ejecutándose correctamente...")
    await app.run_polling()

if name == "__main__":
    asyncio.run(main())

BOT_TOKEN = "1977028208:AAHpkAqAx78Ph5zErJWVfb9Y0wHMwNT9kzs"

USUARIOS_AUTORIZADOS = [5383019921, 1401557612]

CANALES_FIJOS = [
    {
        "id": -1001392767600,
        "nombre": "☠️❌🚧SOBRENATURAL🚧❌☠️",
        "enlace": "https://t.me/+RE-NxTPSc6xmYjNh"
    },
    {
        "id": -1001920805141,
        "nombre": "📥 ADD MY CHANNEL +10K 📥",
        "enlace": "https://t.me/ListaHotBot?start=ar2346575658"
    }
]

ZONA_HORARIA = "America/New_York"

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import USUARIOS_AUTORIZADOS, CANALES_FIJOS, ZONA_HORARIA
from utils.storage import load_json, save_json
from utils.notifier import notificar_admins
from datetime import datetime, timedelta
import pytz
import random

def autorizado(user_id):
    return user_id in USUARIOS_AUTORIZADOS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if autorizado(user_id):
        await update.message.reply_text("✅ Bot funcionando correctamente.")
    else:
        await update.message.reply_text("❌ No estás autorizado para usar este comando.")
        await notificar_admins(
            f"⚠️ Intento no autorizado detectado\n👤 {update.effective_user.full_name} ({user_id})\n💬 /start"
        )

async def estado_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    channels = load_json("data/channels.json")
    fixed = CANALES_FIJOS
    now = datetime.now(pytz.timezone(ZONA_HORARIA)).strftime("%Y-%m-%d %H:%M:%S")
    users = load_json("data/authorized.json")

    estado = f"""📊 Estado del Bot
🕒 Fecha y hora: {now}
📢 Canales activos: {len([c for c in channels if c['activo']])}
📌 Canales fijos: {len(fixed)}
✅ Usuarios autorizados: {len(users)}
""" + "\n".join([f"🔒 {u}" for u in users])

    await update.message.reply_text(estado)

async def agregar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    try:
        canal_id = int(context.args[0])
        nombre = context.args[1]
        enlace = context.args[2]
    except:
        await update.message.reply_text("Uso: /agregar <canal_id> <nombre> <enlace>")
        return

    blacklist = load_json("data/blacklist.json")
    for b in blacklist:
        if b["id"] == canal_id:
            await update.message.reply_text(f"❌ Canal no agregado. En lista negra desde {b['desde']} hasta {b['hasta']}.")
            return

    channels = load_json("data/channels.json")
    if any(c["id"] == canal_id for c in channels):
        await update.message.reply_text("⚠️ El canal ya está agregado.")
    else:
        channels.append({"id": canal_id, "nombre": nombre, "enlace": enlace, "activo": True})
        save_json("data/channels.json", channels)
        await update.message.reply_text("✅ Canal agregado correctamente.")

async def eliminar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    canales = load_json("data/channels.json")
    keyboard = [
        [InlineKeyboardButton(f"{'✅' if c['activo'] else '❌'} {c['nombre']}", callback_data=f"toggle:{c['id']}")]
        for c in canales
    ]
    keyboard.append([InlineKeyboardButton("💾 Guardar cambios", callback_data="guardar")])

    await update.message.reply_text("Selecciona los canales a desactivar:", reply_markup=InlineKeyboardMarkup(keyboard))

async def publicar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return

    encabezado = load_json("data/encabezado.json")
    channels = [c for c in load_json("data/channels.json") if c["activo"]]
    random.shuffle(channels)

    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in channels]
    botones += [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in CANALES_FIJOS]

    markup = InlineKeyboardMarkup(botones)

    success, failed = 0, 0

    for ch in channels:
        try:
            await context.bot.send_animation(
                chat_id=ch["id"],
                animation=encabezado["fileid"],
                caption=encabezado["caption"],
                reply_markup=markup,
                allow_sending_without_reply=True
            )
            success += 1
        except:
            failed += 1
            ch["activo"] = False
            now = datetime.now(pytz.timezone(ZONA_HORARIA))
            hasta = now + timedelta(days=90)
            blacklist = load_json("data/blacklist.json")
            blacklist.append({
                "id": ch["id"],
                "nombre": ch["nombre"],
                "desde": now.strftime("%Y-%m-%d"),
                "hasta": hasta.strftime("%Y-%m-%d")
            })
            save_json("data/blacklist.json", blacklist)
            await notificar_admins(f"⚠️ Canal {ch['nombre']} ({ch['id']}) fue castigado por remover la botonera o permisos.")
    
    save_json("data/channels.json", channels)
    await update.message.reply_text(f"✅ Publicados: {success}, ❌ Fallidos: {failed}")

async def eliminar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    await update.message.reply_text("✅ Botonera eliminada con éxito (simulación).")

async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        nuevo = int(context.args[0])
        users = load_json("data/authorized.json")
        if nuevo not in users:
            users.append(nuevo)
            save_json("data/authorized.json", users)
            await update.message.reply_text("✅ Usuario autorizado.")
        else:
            await update.message.reply_text("⚠️ Ya estaba autorizado.")
    except:
        await update.message.reply_text("Uso: /autorizar <user_id>")

async def revocar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    try:
        uid = int(context.args[0])
        users = load_json("data/authorized.json")
        if uid in users:
            users.remove(uid)
            save_json("data/authorized.json", users)
            await update.message.reply_text("✅ Usuario revocado.")
        else:
            await update.message.reply_text("⚠️ Usuario no estaba autorizado.")
    except:
        await update.message.reply_text("Uso: /revocar <user_id>")

async def listar_autorizados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    users = load_json("data/authorized.json")
    lista = "\n".join([f"🔒 {u}" for u in users])
    await update.message.reply_text(f"Usuarios autorizados:\n{lista}")

async def editar_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    if not update.message.animation:
        await update.message.reply_text("Envía un gif con el nuevo encabezado (caption).")
        return
    nuevo = {
        "type": "gif",
        "fileid": update.message.animation.file_id,
        "caption": update.message.caption or ""
    }
    save_json("data/encabezado.json", nuevo)
    await update.message.reply_text("✅ Encabezado actualizado.")

async def ver_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update.effective_user.id):
        return
    e = load_json("data/encabezado.json")
    await context.bot.send_animation(chat_id=update.effective_chat.id, animation=e["fileid"], caption=e["caption"])

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.storage import load_json, save_json

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    canales = load_json("data/channels.json")

    if data.startswith("toggle:"):
        canal_id = int(data.split(":")[1])
        for c in canales:
            if c["id"] == canal_id:
                c["activo"] = not c["activo"]
        save_json("data/channels.json", canales)

        keyboard = [
            [InlineKeyboardButton(f"{'✅' if c['activo'] else '❌'} {c['nombre']}", callback_data=f"toggle:{c['id']}")]
            for c in canales
        ]
        keyboard.append([InlineKeyboardButton("💾 Guardar cambios", callback_data="guardar")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "guardar":
        save_json("data/channels.json", canales)
        await query.edit_message_text("✅ Cambios guardados.")

    await query.answer()

import json

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

from config import USUARIOS_AUTORIZADOS, BOT_TOKEN
from telegram import Bot

async def notificar_admins(mensaje):
    bot = Bot(token=BOT_TOKEN)
    for uid in USUARIOS_AUTORIZADOS:
        try:
            await bot.send_message(chat_id=uid, text=mensaje)
        except:
            pass

