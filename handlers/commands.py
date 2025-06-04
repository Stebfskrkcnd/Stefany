import os, json
from datetime import datetime
import pytz
import random
import logging
import telegram
import requests
from config import USUARIOS_AUTORIZADOS
from config import ENCABEZADO_FILEID, ENCABEZADO_CAPTION, PATH_BLACKLIST_JSON # type: ignore
from typing import cast
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from telegram import Update
from telegram import Message
from telegram import InputMediaAnimation
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from utils.helpers import load_json, save_json
from telegram.constants import ParseMode
from utils.helpers import limpiar_canales_inactivos
from utils.helpers import git_push

def cargar_autorizados():
    try:
        with open("data/autorizados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

from config import USUARIOS_AUTORIZADOS 
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
    blacklist = load_json("data/blacklist.json", [])
    logging.info("📘 channels.json contiene: %s", channels)

    # Obtener IDs castigados como strings
    blacklist_ids = [str(c["id"]) for c in blacklist]

    # Solo canales activos que no estén en la blacklist
    activos = [c for c in channels if c.get("activo") and str(c["id"]) not in blacklist_ids]

    fixed = CANALES_FIJOS
    now = datetime.now(pytz.timezone(ZONA_HORARIA)).strftime("%Y-%m-%d %H:%M:%S")
    users = USUARIOS_AUTORIZADOS

    estado = f"""📊 Estado del Bot
🕒 Fecha y hora: {now}
✅ Canales activos: {len(activos)}
📌 Canales fijos: {len(fixed)}
👥 Usuarios autorizados: {len(users)}
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
        nombre = lineas[1].strip()
        enlace = "\n".join(lineas[2:]).strip()

        print(">>> Canal recibido:")
        print(f"id: {canal_id}")
        print(f"nombre: {nombre}")
        print(f"enlace: {enlace}")

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

async def ver_canales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Comando /ver_canales recibido")
    user = update.effective_user
    if user is None or user.id not in USUARIOS_AUTORIZADOS:
        if update.message:
            await update.message.reply_text("🚫 No estás autorizad@ para usar este comando.")
        return

    with open("data/channels.json", "r", encoding="utf-8") as f:
        canales = json.load(f)

    canales_activos = [c for c in canales if c.get("activo", True)]

    if not canales_activos:
        await update.message.reply_text("No hay canales activos actualmente.") # type: ignore
        return

    def dividir_lista(lista, n):
        for i in range(0, len(lista), n):
            yield lista[i:i + n]

    total_suscriptores = 0
    bloques = list(dividir_lista(canales_activos, 10))

    for bloque in bloques:
        mensaje = "📢 <b>Lista de canales participando:</b>\n\n"
        for canal in bloque:
            canal_id = canal["id"]
            nombre = canal["nombre"]
            enlace = canal["enlace"]

            try:
                subs = await context.bot.get_chat_member_count(canal_id)
            except TelegramError:
                subs = "Desconocido"

            mensaje += f"<b>📌 Nombre:</b> {nombre}\n"
            mensaje += f"<b>🆔 ID:</b> {canal_id}\n"
            mensaje += f"<b>🔗 Enlace:</b> {enlace}\n"
            mensaje += f"<b>👥 Subscriptores:</b> {subs}\n\n"

            if isinstance(subs, int):
                total_suscriptores += subs

        await update.message.reply_text(mensaje, parse_mode="HTML", disable_web_page_preview=True) # type: ignore

    # Mensaje final con totales
    resumen = f"🔢 <b>Total participando:</b> {len(canales_activos)} canales\n"
    resumen += f"👥 <b>Total subscriptores:</b> {total_suscriptores}"
    await update.message.reply_text(resumen, parse_mode="HTML", disable_web_page_preview=True) # type: ignore

async def eliminar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if not autorizado(user.id):
        return await message.reply_text("❌ No estás autorizado.")

    canales = load_json("data/channels.json")
    botones = []

    for canal in canales:
        botones.append([
            InlineKeyboardButton(
                text=f"❌ {canal['nombre']}",
                callback_data=f"eliminar_canal_{canal['id']}"
            )
        ])

    if not botones:
        return await message.reply_text("⚠️ No hay canales para eliminar.")

    # ✅ Agrega el botón "Guardar cambios"
    botones.append([
        InlineKeyboardButton("📝 Guardar cambios", callback_data="guardar")
    ])

    reply_markup = InlineKeyboardMarkup(botones)
    await message.reply_text("🗑️ Selecciona los canales a eliminar:", reply_markup=reply_markup)

async def notificar_admins(msg):
    print(f"[ADMIN] {msg}")

async def publicar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    print(f"✅ Entró a publicar_botonera a las {datetime.now().strftime('%H:%M:%S')}")
    import uuid
    print("🆔 ID de instancia:", uuid.uuid4())
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

    blacklist = load_json("data/blacklist.json", [])

    print("✅ Canales cargados:", json.dumps(channels, indent=2))

    for ch in channels:
        try:
            print(f"📤 Enviando a canal: {ch['nombre']} ({ch['id']}) con enlace: {ch['enlace']}")
            msg = await context.bot.send_animation(
                chat_id=ch["id"],
                animation=ENCABEZADO_FILEID,
                caption=ENCABEZADO_CAPTION,
                reply_markup=markup,
                allow_sending_without_reply=True
            )
            ch["message_id"] = msg.message_id
            success += 1
        except Exception as e:
            print(f"❌ EXCEPCIÓN al enviar a {ch['nombre']} ({ch['id']}):", e)
            logging.exception(f"⚠️ Error publicando en canal {ch['nombre']} ({ch['id']})")
            failed += 1
            ch["activo"] = False

            now = datetime.now(pytz.timezone(ZONA_HORARIA))
            hasta = now + timedelta(days=90)

            # 🛡️ Solo castiga si no está ya en la blacklist
            if not any(str(c["id"]) == str(ch["id"]) for c in blacklist):
                ch["desde"] = now.strftime("%Y-%m-%d")
                ch["hasta"] = hasta.strftime("%Y-%m-%d")
                blacklist.append(ch)
                save_json("data/blacklist.json", blacklist)
                await notificar_admins(
                    f"⚠️ Canal {ch['nombre']} ({ch['id']}) fue castigado por fallo al enviar."
                )

            await notificar_admins(
                f"⚠️ Canal {ch['nombre']} ({ch['id']}) fue castigado por remover la botonera o no permitir publicación."
        )
        limpiar_canales_inactivos()
        git_push("Auto limpieza: canales inactivos eliminados tras castigo")

    if update.message:
        message = update.message #✅ Esta linea lo arregla
        await message.reply_text(
        f"✅ Publicados: {success}, ❌ Fallidos: {failed}"
    )
        save_json("data/channels.json", channels)

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

    success = 0
    fallos = []
    blacklist = load_json("data/blacklist.json", [])
    channels = load_json("data/channels.json")

    for ch in channels:
        try:
            if ch.get("message_id"):
                await context.bot.delete_message(
                    chat_id=ch["id"],
                    message_id=ch["message_id"]
                )
                success += 1
        except Exception as e:
            motivo = "eliminaron manualmente la publicación" if "message to delete not found" in str(e) else "el bot no tenía permisos"
            ch["activo"] = False
            ch["desde"] = datetime.now(pytz.timezone(ZONA_HORARIA)).strftime("%Y-%m-%d")
            ch["hasta"] = (datetime.now(pytz.timezone(ZONA_HORARIA)) + timedelta(days=90)).strftime("%Y-%m-%d")
            ch["motivo"] = motivo
            fallos.append(ch)
            blacklist.append(ch)
        finally:
            ch.pop("message_id", None)

    save_json("data/channels.json", channels)
    save_json("data/blacklist.json", blacklist)
    await message.reply_text(
    f"🗑️ Botonera eliminada de {success} canales.\n"
    f"❌ Fallos: {len(fallos)} canal(es)."
)

    if fallos:
        detalles = "\n\n".join(
            f"🔴 {c['nombre']} ({c['id']})\n🔗 {c['enlace']}\n❌ Motivo: {c['motivo']}"
            for c in fallos
        )
        await message.reply_text(f"📋 Detalles de los fallos:\n\n{detalles}")
    

print("⚙️ Ejecutando /descastigar")
async def descastigar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not isinstance(message, Message):
        return
    
    user = update.effective_user
    if user is None or user.id not in USUARIOS_AUTORIZADOS:
        return await message.reply_text("❌ No estás autorizado.")
    
    if not context.args:
        return await message.reply_text("Uso: /descastigar <id del canal>")

    try:
        canal_id = context.args[0]

        blacklist = load_json("data/blacklist.json", [])
        nueva_blacklist = [c for c in blacklist if str(c["id"]) != canal_id]

        if len(blacklist) == len(nueva_blacklist):
            return await message.reply_text("⚠️ Ese canal no estaba en la blacklist.")

        save_json("data/blacklist.json", nueva_blacklist)
        await message.reply_text("✅ Canal removido de la blacklist.")

    except Exception as e:
        print("⚠️ EXCEPCIÓN en /descastigar:", e)
        return await message.reply_text("❌ Error inesperado al intentar descastigar.")

async def ver_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user is None or not autorizado(user.id):
        return await message.reply_text("❌ No estás autorizado.") # type: ignore

    blacklist = load_json("data/blacklist.json", [])
    
    if not blacklist:
        return await message.reply_text("🧹 La blacklist está vacía.") # type: ignore

    texto = "⛔️ Canales en blacklist:\n\n"
    for ch in blacklist:
        texto += (
            f"🔒 <b>{ch.get('nombre', 'Sin nombre')}</b>\n"
            f"🆔 ID: <code>{ch.get('id')}</code>\n"
            f"🔗 Enlace: {ch.get('enlace', 'N/A')}\n"
            f"📆 Desde: {ch.get('desde', '¿?')}  Hasta: {ch.get('hasta', '¿?')}\n"
            f"📌 Motivo: {ch.get('motivo', 'No especificado')}\n"
            f"──────────────\n"
        )

    await message.reply_text(texto, parse_mode=ParseMode.HTML) # type: ignore

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
