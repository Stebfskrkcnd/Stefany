import os, json

import pytz
import random
import logging
from config import ENCABEZADO_FILEID, ENCABEZADO_CAPTION
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from telegram import Update
from telegram import InputMediaAnimation
from telegram.ext import ContextTypes
from utils.helpers import load_json, save_json

def cargar_autorizados():
    try:
        with open("data/autorizados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

USUARIOS_AUTORIZADOS = load_json("data/autorizados.json", [])
ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/New_York")

# Si quieres usar CANALES_FIJOS como JSON string desde una variable:
import json
try:
    CANALES_FIJOS = json.loads(os.getenv("CANALES_FIJOS", "[]"))
except:
    CANALES_FIJOS = []

def autorizado(user_id):
    return user_id in USUARIOS_AUTORIZADOS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return  # No se puede procesar sin usuario o mensaje

    user_id = user.id

    if autorizado(user_id):
        await message.reply_text("✅ Bot funcionando correctamente.")
    else:
        await message.reply_text("❌ No estás autorizado para usar este comando.")
        await notificar_admins(
            f"⚠️ Intento no autorizado detectado\n🧑 {user.first_name} {user.last_name or ''} ({user.id})"
        )
async def estado_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    channels = load_json("data/channels.json")
    logging.info("📘 channels.json contiene: %s", channels)

    fixed = CANALES_FIJOS
    now = datetime.now(pytz.timezone(ZONA_HORARIA)).strftime("%Y-%m-%d %H:%M:%S")
    users = USUARIOS_AUTORIZADOS

    estado = f"""📊 Estado del Bot
🕒 Fecha y hora: {now}
📌 Canales activos: {len([c for c in channels if c['activo']])}
📍 Canales fijos: {len(fixed)}
🛡️ Usuarios autorizados: {len(users)}
""" + "\n".join([f"🔐 {u}" for u in users])

    await message.reply_text(estado)

async def agregar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message  # Esto sí garantiza que no sea None

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    try:
        texto = message.text or ""
        lineas = texto.strip().split("\n")[1:]
        if len(lineas) < 3:
            await message.reply_text("❗Uso incorrecto. Formato esperado:\n/agregar\n<canal_id>\n<enlace>\n<nombre>")
            return

        canal_id = lineas[0].strip()
        enlace = lineas[1].strip()
        nombre = "\n".join(lineas[2:]).strip()

        print(">>> Canal recibido:")
        print(f"id: {canal_id}")
        print(f"enlace: {enlace}")
        print(f"nombre: {nombre}")

        # Verificar blacklist
        blacklist = load_json("data/blacklist.json")
        for b in blacklist:
            if b["id"] == canal_id:
                await message.reply_text(
                    f"❌ Canal no agregado. En lista negra desde {b['desde']} hasta {b['hasta']}."
                )
                return

        # Verificar si ya existe
        channels = load_json("data/channels.json")
        if any(c["id"] == canal_id for c in channels):
            await message.reply_text("⚠️ El canal ya está agregado.")
            return

        channels.append({
            "id": canal_id,
            "nombre": nombre,
            "enlace": enlace,
            "activo": True
        })

        save_json("data/channels.json", channels)
        await message.reply_text("✅ Canal agregado correctamente.")

    except Exception as e:
        await message.reply_text(f"❌ Error en agregar: {e}")

async def eliminar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    canales = load_json("data/channels.json")
    keyboard = [
        [InlineKeyboardButton(f"{'✅' if c['activo'] else '❌'} {c['nombre']}", callback_data=f"toggle:{c['id']}")]
        for c in canales
    ]

    keyboard.append([InlineKeyboardButton("📝 Guardar cambios", callback_data="guardar")])

    await message.reply_text("Selecciona los canales a desactivar:", reply_markup=InlineKeyboardMarkup(keyboard))

async def notificar_admins(msg):
    print(f"[ADMIN] {msg}")

async def publicar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user is None or not autorizado(user.id):
        return

    channels = [
        c for c in load_json("data/channels.json")
        if c["activo"] and c["id"] not in [cf["id"] for cf in CANALES_FIJOS]
    ]
    random.shuffle(channels)
    botones = [
        [InlineKeyboardButton(c["nombre"], url=c["enlace"])]
        for c in channels
    ]
    botones += [
        [InlineKeyboardButton(c["nombre"], url=c["enlace"])]
        for c in CANALES_FIJOS
    ]

    markup = InlineKeyboardMarkup(botones)

    success, failed = 0, 0

    for ch in channels:
        try:
            msg = await context.bot.send_animation(
                chat_id=ch["id"],
                animation=ENCABEZADO_FILEID,
                caption=ENCABEZADO_CAPTION,
                reply_markup=markup,
                allow_sending_without_reply=True
            )
            ch["message_id"] = msg.message_id  # 🔴 Guarda el ID del mensaje
            success += 1
        except Exception:
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
            await notificar_admins(
                f"⚠️ Canal {ch['nombre']} ({ch['id']}) fue castigado por remover la botonera o no permitir publicación."
            )
    
    save_json("data/channels.json", channels)

    if update.message:
        await update.message.reply_text(
        f"✅ Publicados: {success}, ❌ Fallidos: {failed}"
    )

    encabezado = {
    "fileid": ENCABEZADO_FILEID,
    "caption": ENCABEZADO_CAPTION
}

async def ver_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    try:
        await context.bot.send_animation(
            chat_id=user.id,
            animation=ENCABEZADO_FILEID,
            caption=ENCABEZADO_CAPTION,
            allow_sending_without_reply=True
        )
    except Exception as e:
        await message.reply_text(f"❌ Error al mostrar el encabezado: {e}")

async def eliminar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    channels = load_json("data/channels.json")

    success = 0
    for ch in channels:
        if ch.get("activo") and "message_id" in ch:
            try:
                await context.bot.delete_message(chat_id=ch["id"], message_id=ch["message_id"])
                success += 1
            except:
                pass  # Ya fue eliminada manualmente
            ch.pop("message_id", None)  # Limpia aunque falle

    save_json("data/channels.json", channels)

    await message.reply_text(f"🗑 Botonera eliminada de {success} canales.")

async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    user_id = user.id
    if not autorizado(user_id):
        return

    try:
        args = context.args or []
        nuevo_id = int(args[0])
    except (IndexError, ValueError):
        await message.reply_text("Uso: /autorizar <user_id>")
        return

    if nuevo_id in USUARIOS_AUTORIZADOS:
        await message.reply_text("✅ Este usuario ya está autorizado.")
        return

    USUARIOS_AUTORIZADOS.append(nuevo_id)

    with open("data/autorizados.json", "w", encoding="utf-8") as f:
        json.dump(USUARIOS_AUTORIZADOS, f)

    await message.reply_text(f"✅ Usuario {nuevo_id} autorizado correctamente.")

    # Guardar en archivo
    with open("data/autorizados.json", "w", encoding="utf-8") as f:
        json.dump(USUARIOS_AUTORIZADOS, f)

    await message.reply_text(f"✅ Usuario {nuevo_id} autorizado correctamente.")

async def revocar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    try:
        args = context.args or []
        uid = int(args[0])
    except (IndexError, ValueError):
        await message.reply_text("Uso: /revocar <user_id>")
        return

    users = load_json("data/autorizados.json")

    if uid in users:
        users.remove(uid)
        save_json("data/autorizados.json", users)

        # También actualiza la lista en memoria si es necesario
        USUARIOS_AUTORIZADOS.clear()
        USUARIOS_AUTORIZADOS.extend(users)

        await message.reply_text(f"✅ Usuario {uid} revocado.")
    else:
        await message.reply_text("⚠️ Ese usuario no estaba autorizado.")

async def listar_autorizados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return

    users = load_json("data/autorizados.json")
    lista = "\n".join([f"🔐 {u}" for u in users])

    await message.reply_text(f"👤 Usuarios autorizados:\n{lista}")
