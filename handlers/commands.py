import os

import pytz
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import load_json

import json

def cargar_autorizados():
    try:
        with open("data/autorizados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

USUARIOS_AUTORIZADOS = cargar_autorizados()
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
    users = USUARIOS_AUTORIZADOS
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

print(">>> Args recibidos:", context.args)
try:
        canal_id = int(context.args[0])
        nombre = context.args[1]
        enlace = context.args[2]
except Exception as e:
    await update.message.reply_text(f"Error en agregar: {e}")
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
    user_id = update.effective_user.id
    if not autorizado(user_id):
        return

    try:
        nuevo_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Uso: /autorizar <user_id>")
        return

    if nuevo_id in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("✅ Este usuario ya está autorizado.")
        return

    USUARIOS_AUTORIZADOS.append(nuevo_id)

    # Guardar en archivo
    with open("data/autorizados.json", "w", encoding="utf-8") as f:
        json.dump(USUARIOS_AUTORIZADOS, f)

    await update.message.reply_text(f"✅ Usuario {nuevo_id} autorizado correctamente.")

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