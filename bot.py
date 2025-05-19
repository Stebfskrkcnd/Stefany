from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

import json
import os
import random
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from pytz import timezone

async def notificar_programacion(app):
    scheduler.add_job(
        lambda: asyncio.create_task(publicar_botonera_diaria(app)),
        "cron",
        hour=18, minute=30, timezone="US/Eastern"  # Edita si necesitas otro horario
    )


 # ✅ Publicación automática diaria con blacklist
async def publicar_botonera_diaria(app):
    print("⏰ Ejecutando publicación automática de botonera")
    if not os.path.exists(CANAL_ARCHIVO):
        print("⚠️ No se encontró el archivo de canales.")
        return

    with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
        canales = json.load(f)

    if not canales:
        print("⚠️ No hay canales para publicar.")
        return

AsyncIOScheduler(timezone=timezone("US/Eastern"))

scheduler = AsyncIOScheduler()
scheduler.add_job(
    lambda: asyncio.create_task(publicar_botonera_diaria(app)),
    trigger="cron",
    hour=18,
    minute=30,
    id="botonera_diaria",
    replace_existing=True
)

scheduler.start()
# === Blacklist ===
BLACKLIST_FILE = "blacklist.json"

def cargar_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_blacklist(lista):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def limpiar_blacklist():
    ahora = datetime.now()
    lista = cargar_blacklist()
    lista_nueva = [c for c in lista if datetime.fromisoformat(c["hasta"]) > ahora]
    if len(lista) != len(lista_nueva):
        guardar_blacklist(lista_nueva)

# === CONFIGURACIÓN ===
TOKEN = "1977028208:AAHpkAqAx78Ph5zErJWVfb9Y0wHMwNT9kzs"
ADMIN_IDS = [5383019921, 1401557612]
CANAL_ARCHIVO = "channels.json"
USUARIOS_FILE = "autorizados.json"
ENCABEZADO_FILE = "encabezado.txt"

# ✅ Variable global
mensajes_publicados = []

# === Mostrar programación en consola y notificar a admins por Telegram ===
for job in scheduler.get_jobs():
    print(f"⏳ Job '{job.id}' programado para: {job.next_run_time}")

# ✅ Notificar a admins vía Telegram la hora programada
async def notificar_programacion(app):
    print("⚙️ Ejecutando función notificar_programacion")

    for job in scheduler.get_jobs():
        hora = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        for admin_id in ADMIN_IDS:
            try:
                await app.bot.send_message(
                    chat_id=admin_id,
                    text=f"⏰ Botonera programada para: *{hora}*",
                    parse_mode="Markdown"
                )
                print(f"✅ Notificación enviada a {admin_id}")
            except Exception as e:
                print(f"❌ Error notificando al admin {admin_id}: {e}")

# === FUNCIONES BASE ===

# ✅ Usuarios autorizados por defecto
USUARIOS_AUTORIZADOS = [1401557612, 5383019921]

# ✅ Cargar usuarios autorizados
def cargar_autorizados():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(USUARIOS_AUTORIZADOS, f, ensure_ascii=False, indent=2)
        return USUARIOS_AUTORIZADOS

# ✅ Guardar usuarios autorizados
def guardar_autorizados(lista):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

# ✅ Logger: intento no autorizado
async def log_intento_no_autorizado(update: Update, comando: str):
    user = update.effective_user
    mensaje = (
        f"⚠️ *Intento no autorizado detectado:*\n\n"
        f"👤 Usuario: {user.full_name} (`{user.id}`)\n"
        f"📢 Comando: `{comando}`"
    )
    for admin_id in ADMIN_IDS:
        try:
            await update.get_bot().send_message(
                chat_id=admin_id,
                text=mensaje,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ No se pudo enviar el log a {admin_id} → {e}")


# === COMANDOS ===

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()

    if user_id not in autorizados:
        await log_intento_no_autorizado(update, "/start")
        await update.message.reply_text("❌ No estás autorizado para usar este bot.")
        return

    await update.message.reply_text("Hola, The Witch. El bot está listo para usarse.🔮")

# /listar_autorizados
async def listar_autorizados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()

    if user_id not in autorizados:
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    texto = "🆔 *Usuarios autorizados:*\n"
    texto += "\n".join([f"- `{uid}`" for uid in autorizados])
    await update.message.reply_text(texto, parse_mode="Markdown")

# /autorizar ID
async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    autorizados = cargar_autorizados()
    requester_id = update.effective_user.id

    if requester_id not in autorizados:
        await log_intento_no_autorizado(update, "/autorizar")
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /autorizar ID")
        return

    try:
        nuevo_id = int(context.args[0])
    except:
        await update.message.reply_text("ID inválido.")
        return

    if nuevo_id in autorizados:
        await update.message.reply_text("Ese usuario ya está autorizado.")
        return

    autorizados.append(nuevo_id)
    guardar_autorizados(autorizados)
    await update.message.reply_text(f"✅ Usuario {nuevo_id} autorizado correctamente.")

# /ver_blacklist — Muestra los canales actualmente en la lista negra
async def ver_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("No tienes permisos para ver la lista negra.")
        return

    if not os.path.exists("blacklist.json"):
        await update.message.reply_text("La lista negra está vacía.")
        return

    with open("blacklist.json", "r", encoding="utf-8") as f:
        blacklist = json.load(f)

    if not blacklist:
        await update.message.reply_text("La lista negra está vacía.")
        return

    texto = "🚫 *Canales en lista negra:*\n\n"
    for canal in blacklist:
        texto += f"• {canal['nombre']} (`{canal['id']}`)\nHasta: `{canal['hasta']}`\n\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

# /fileid → obtiene el file_id de un GIF, foto, video o sticker
async def fileid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg.reply_to_message:
        await msg.reply_text("❌ Debes responder al GIF, foto o video para obtener su file_id.")
        return

    media = msg.reply_to_message

    if media.photo:
        file_id = media.photo[-1].file_id
    elif media.video:
        file_id = media.video.file_id
    elif media.animation:
        file_id = media.animation.file_id
    elif media.sticker:
        file_id = media.sticker.file_id
    else:
        await msg.reply_text("❌ No se encontró un archivo multimedia válido.")
        return

    await msg.reply_text(f"📎 *file_id:* `{file_id}`", parse_mode="Markdown")

# /agregar Nombre https://t.me/enlace -1001234567890
async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()
    if user_id not in autorizados:
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("❌ Uso obligatorio: /agregar Nombre https://t.me/enlace -100XXXXXXXXXX")
        return

    try:
        canal_id = int(context.args[-1])
    except:
        await update.message.reply_text("❌ El ID debe comenzar con -100 y contener solo números.")
        return

    enlace = context.args[-2]
    nombre = " ".join(context.args[:-2])

    import re
    patron = r"^https://t\.me/[\w\-\+]+$"
    if not re.match(patron, enlace):
        await update.message.reply_text("❌ El enlace debe tener formato válido: https://t.me/nombre")
        return
    
    canales = []
    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)

    for c in canales:
        if c["id"] == canal_id or c["enlace"] == enlace or c["nombre"].lower() == nombre.lower():
            await update.message.reply_text("⚠️ Ese canal ya está agregado.")
            return

    nuevo = {
        "id": canal_id,
        "nombre": nombre,
        "enlace": enlace
    }

    canales.append(nuevo)
    # Verificar si está en la blacklist
    blacklist = cargar_blacklist()
    for canal_baneado in blacklist:
        if canal_baneado["id"] == canal_id:
            hasta = canal_baneado["hasta"]
            nombre = canal_baneado.get("nombre", "Desconocido")
            await update.message.reply_text(
                f"⛔ El canal *{nombre}* (`{canal_id}`) está en la lista negra.\n"
                f"🗓️ Castigo activo hasta: `{hasta}`\n"
                f"No puedes agregarlo hasta que expire la sanción.",
                parse_mode="Markdown"
            )
            return
    with open(CANAL_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(canales, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ Canal *{nombre}* agregado correctamente con ID `{canal_id}`",
        parse_mode="Markdown"
    )

# === ELIMINACIÓN INTERACTIVA ===

# === Eliminación con botones interactivos ===
canales_temporales = {}

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🧨 /eliminar ejecutado")
    user_id = update.effective_user.id

    if user_id not in cargar_autorizados():
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    if not os.path.exists(CANAL_ARCHIVO):
        await update.message.reply_text("No hay canales guardados.")
        return

    with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
        canales = json.load(f)

    if not canales:
        await update.message.reply_text("Lista de canales vacía.")
        return

    canales_temporales[user_id] = {"canales": canales.copy(), "eliminados": []}

    teclado = []
    for canal in canales:
        boton = InlineKeyboardButton(
            f"✅ {canal['nombre']}",
            callback_data=f"toggle::{canal['id']}"
        )
        teclado.append([boton])

    teclado.append([InlineKeyboardButton("💾 Guardar cambios", callback_data="guardar")])
    markup = InlineKeyboardMarkup(teclado)

    await update.message.reply_text(
        "🗂️ *Selecciona los canales a eliminar (tócalos para cambiar):*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def callback_eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in canales_temporales:
        await query.edit_message_text("⚠️ No hay selección activa. Usa /eliminar primero.")
        return

    data = query.data
    estado = canales_temporales[user_id]

    if data == "guardar":
        canales_final = [
            c for c in estado["canales"]
            if c["id"] not in estado["eliminados"]
        ]
        cantidad = len(estado["canales"]) - len(canales_final)

        with open(CANAL_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(canales_final, f, ensure_ascii=False, indent=2)

        del canales_temporales[user_id]
        await query.edit_message_text(f"✅ {cantidad} canal(es) eliminado(s) correctamente.")
        return

    # Extrae el ID del botón
    _, canal_id_str = data.split("::", 1)
    canal_id = int(canal_id_str)

    if canal_id in estado["eliminados"]:
        estado["eliminados"].remove(canal_id)
    else:
        estado["eliminados"].append(canal_id)

    teclado = []
    for canal in estado["canales"]:
        marcado = "❌" if canal["id"] in estado["eliminados"] else "✅"
        boton = InlineKeyboardButton(
            f"{marcado} {canal['nombre']}",
            callback_data=f"toggle::{canal['id']}"
        )
        teclado.append([boton])

    teclado.append([InlineKeyboardButton("💾 Guardar cambios", callback_data="guardar")])
    markup = InlineKeyboardMarkup(teclado)

    await query.edit_message_reply_markup(reply_markup=markup)


# === OTROS COMANDOS ===

# === Función auxiliar para obtener destinos dinámicos ===
def obtener_destinos():
    if not os.path.exists(CANAL_ARCHIVO):
        return []

    with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
        canales = json.load(f)

    destinos = [
        c["id"]
        for c in canales
        if "SOBRENATURAL" not in c["nombre"] and "ADD MY CHANNEL" not in c["nombre"]
    ]
    return destinos

# === BOTONERA PRINCIPAL ===
# ================================
# 🔁 Funciones auxiliares
# ================================

# Obtener la lista de canales dinámicamente (excluyendo los fijos)
def obtener_destinos():
    if not os.path.exists(CANAL_ARCHIVO):
        return []
    
    with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
        canales = json.load(f)

    destinos = [
        c["id"]
        for c in canales
        if "SOBRENATURAL" not in c["nombre"] and "ADD MY CHANNEL" not in c["nombre"]
    ]
    return destinos

# ✅ /botonera con soporte para encabezado GIF o texto
async def botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bloquear si viene de canal fijo
    canal_fijo_ids = [
        -1002050701908,  # SOBRENATURAL
        -1009999999999   # ADD MY CHANNEL (reemplaza con el real)
    ]

    chat_id = update.effective_chat.id
    if chat_id in canal_fijo_ids:
        return  # No publica si es uno de los fijos

    user_id = update.effective_user.id
    autorizados = cargar_autorizados()
    if user_id not in autorizados:
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    if not os.path.exists(CANAL_ARCHIVO):
        await update.message.reply_text("No hay canales aún.")
        return

    try:
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)
    except json.JSONDecodeError:
        await update.message.reply_text("⚠️ El archivo de canales está dañado.")
        return

    if not canales:
        await update.message.reply_text("Lista de canales vacía.")
        return

    # Separar fijos y mezclar resto
    fijo1 = next((c for c in canales if "SOBRENATURAL" in c["nombre"]), None)
    fijo2 = next((c for c in canales if "ADD MY CHANNEL" in c["nombre"]), None)
    canales = [c for c in canales if c not in [fijo1, fijo2]]
    random.shuffle(canales)
    if fijo1: canales.append(fijo1)
    if fijo2: canales.append(fijo2)

    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in canales]
    teclado = InlineKeyboardMarkup(botones)
    encabezado = obtener_encabezado()
    # Enviar encabezado con botones
    if isinstance(encabezado, dict) and encabezado.get("type") == "gif":
        msg = await update.message.reply_animation(
            animation=encabezado["file_id"],
            caption=encabezado["caption"],
            reply_markup=teclado
        )
    else:
        msg = await update.message.reply_text(
            encabezado if isinstance(encabezado, str) else encabezado.get("caption", ""),
            reply_markup=teclado
        )

    # Eliminar después de 23 horas
    await asyncio.sleep(82800)
    try:
        await msg.delete()
        await update.message.delete()
    except:
        pass

    # Mezclar y volver a añadir los fijos al final
    random.shuffle(canales)
    if fijo1: canales.append(fijo1)
    if fijo2: canales.append(fijo2)

    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in canales]
    teclado = InlineKeyboardMarkup(botones)

    if update.message.reply_to_message:
        media = update.message.reply_to_message
        if media.photo:
            msg = await update.message.reply_photo(photo=media.photo[-1].file_id, caption=encabezado, reply_markup=teclado)
        elif media.video:
            msg = await update.message.reply_video(video=media.video.file_id, caption=encabezado, reply_markup=teclado)
        elif media.animation:
            msg = await update.message.reply_animation(animation=media.animation.file_id, caption=encabezado, reply_markup=teclado)
        else:
            msg = await update.message.reply_text(encabezado, reply_markup=teclado)
    else:
        msg = await update.message.reply_text(encabezado, reply_markup=teclado)

async def manejar_canal_invalido(canal, app, motivo):
    canal_id = canal.get("id")
    nombre = canal.get("nombre")

    # Cargar canales y blacklist
    canales = []
    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)

    # Eliminar de la lista principal
    canales = [c for c in canales if c.get("id") != canal_id]
    with open(CANAL_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(canales, f, ensure_ascii=False, indent=2)

    # Añadir a blacklist 90 días
    fecha_rehabilitacion = (datetime.now() + timedelta(days=90)).isoformat()
    blacklist = cargar_blacklist()
    blacklist.append({
        "id": canal_id,
        "nombre": nombre,
        "enlace": canal.get("enlace"),
        "hasta": fecha_rehabilitacion
    })
    guardar_blacklist(blacklist)

    # Notificar a los admins
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"⚠️ Canal *{nombre}* (`{canal_id}`) fue eliminado de la botonera por:\n`{motivo}`\n\n"
                     f"Agregado a *blacklist* por 90 días.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ No se pudo notificar al admin {admin_id}: {e}")

# /revocar ID
async def revocar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    autorizados = cargar_autorizados()
    requester_id = update.effective_user.id

    if requester_id not in autorizados:
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /revocar ID")
        return

    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("ID inválido.")
        return

    if uid not in autorizados:
        await update.message.reply_text("Ese usuario no está en la lista.")
        return

    autorizados.remove(uid)
    guardar_autorizados(autorizados)
    await update.message.reply_text(f"🚫 Usuario {uid} revocado correctamente.")

# /test_botonera
async def test_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in cargar_autorizados():
        await update.message.reply_text("❌ No estás autorizado para hacer pruebas.")
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    try:
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al leer canales: {e}")
        return

# /borrar_botonera
async def borrar_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in cargar_autorizados():
        await update.message.reply_text("❌ No estás autorizado para usar este comando.")
        return

    eliminados = 0
    for chat_id, message_id in mensajes_publicados:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            eliminados += 1
        except Exception as e:
            print(f"⚠️ No se pudo borrar mensaje en {chat_id}: {e}")

    mensajes_publicados.clear()
    await update.message.reply_text(f"🗑️ {eliminados} mensajes de botonera eliminados.")

    # /test_botonera
async def test_botonera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mensajes_publicados  # <-- Esta línea debe ir al principio

    if update.effective_user.id not in cargar_autorizados():
        await update.message.reply_text("❌ No estás autorizado para usar este comando.")
        return

    if not os.path.exists(CANAL_ARCHIVO):
        await update.message.reply_text("No hay canales disponibles.")
        return

    with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
        canales = json.load(f)

    # Separar los fijos
    fijo1 = next((c for c in canales if "SOBRENATURAL" in c["nombre"]), None)
    fijo2 = next((c for c in canales if "ADD MY CHANNEL" in c["nombre"]), None)
    canales = [c for c in canales if c not in [fijo1, fijo2]]
    random.shuffle(canales)
    if fijo1: canales.append(fijo1)
    if fijo2: canales.append(fijo2)

    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in canales]
    teclado = InlineKeyboardMarkup(botones)

    destinos = obtener_destinos()
    mensajes = []

    encabezado = obtener_encabezado()

    for chat_id in destinos:
        try:
            if encabezado.get("type") == "gif" and encabezado.get("file_id"):
                msg = await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=encabezado["file_id"],
                    caption=encabezado["caption"],
                    reply_markup=teclado,
                    parse_mode="Markdown"
                )
            else:
                msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=encabezado.get("caption", encabezado),
                    reply_markup=teclado,
                    parse_mode="Markdown"
                )
            
            mensajes.append((chat_id, msg.message_id))
            print(f"✅ Enviado a {chat_id}")

        except Exception as e:
            print(f"❌ Error en {chat_id}: {e}")

    mensajes_publicados = mensajes
    await update.message.reply_text("✅ Botonera enviada en modo prueba.")

# === MANEJO DE ERRORES ===

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("❌ ERROR DETECTADO:", context.error)

# ✅ Establecer comandos del menú /
async def set_bot_commands(app):
    comandos = [
        BotCommand("start", "Iniciar el bot"),
        BotCommand("autorizar", "Autoriza un usuario"),
        BotCommand("revocar", "Revoca un usuario"),
        BotCommand("listar_autorizados", "Ver usuarios autorizados"),
        BotCommand("agregar", "Agregar canal manualmente"),
        BotCommand("eliminar", "Eliminar canal con botones"),
        BotCommand("botonera", "Enviar botonera de canales"),
        BotCommand("editar_encabezado", "Editar texto principal de la botonera"),
        BotCommand("ver_encabezado", "Ver encabezado actual de la botonera"),
        BotCommand("estado", "Ver estado actual del bot"),
        BotCommand("ver_blacklist", "Ver canales bloqueados temporalmente")
    ]
    await app.bot.set_my_commands(comandos)

# ✅ Reenvío de mensaje desde canal → guarda ID, nombre y enlace
async def reenviado_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()

    if user_id not in autorizados:
        await mensaje.reply_text("No estás autorizado para usar esta función.")
        return

    # Solo si es reenviado desde un canal
    if not mensaje.forward_from_chat or mensaje.forward_from_chat.type != "channel":
        return

    canal_chat = mensaje.forward_from_chat
    canal_id = canal_chat.id
    nombre = canal_chat.title
    username = canal_chat.username

    if not username:
        await mensaje.reply_text("⚠️ Este canal no tiene un @username público.")
        return

    enlace = f"https://t.me/{username}"

    canales = []
    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)


    # Verificar si ya está
    for c in canales:
        if c.get("id") == canal_id or c["enlace"] == enlace:
            await mensaje.reply_text("⚠️ Ese canal ya está agregado.")
            return

    canales.append({
        "id": canal_id,
        "nombre": nombre,
        "enlace": enlace
    })

    with open(CANAL_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(canales, f, ensure_ascii=False, indent=2)

    await mensaje.reply_text(f"✅ Canal *{nombre}* añadido correctamente con ID `{canal_id}`", parse_mode="Markdown")

# === SETUP FINAL ===

print("Bot funcionando correctamente")
application = ApplicationBuilder().token("1977028208:AAHpkAqAx78Ph5zErJWVfb9Y0wHMwNT9kzs").build()

# ✅ Configuraciones iniciales
application.add_error_handler(error_handler)

async def post_init(app):
    await set_bot_commands(app)
    await notificar_programacion(app)

application.post_init = post_init
# /editar_encabezado Texto nuevo
async def editar_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()

    if user_id not in autorizados:
        await update.message.reply_text("No estás autorizada para usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /editar_encabezado Texto nuevo del encabezado")
        return

    nuevo_encabezado = " ".join(context.args)

    with open(ENCABEZADO_FILE, "w", encoding="utf-8") as f:
        f.write(nuevo_encabezado.strip())

    await update.message.reply_text("✅ Encabezado actualizado correctamente.")
# === ENCABEZADO PERSONALIZADO ===

ENCABEZADO_FILE = "encabezado.txt"

# ✅ Leer encabezado desde archivo, con soporte para GIF personalizado
def obtener_encabezado():
    if not os.path.exists(ENCABEZADO_FILE):
        return {"type": "gif", "file_id": "", "caption": "❌ATTENTION - The best channels for adults have arrived 😋 ⛔️Content filtered for a limited time."}

    with open(ENCABEZADO_FILE, "r", encoding="utf-8") as f:
        contenido = f.read().strip()

    if contenido.startswith("[GIF] "):
        partes = contenido.split("\n", 1)
        file_id = partes[0].split()[1] if len(partes) > 0 else ""
        caption = partes[1] if len(partes) > 1 else ""
        return {"type": "gif", "file_id": file_id, "caption": caption}

    # Si no hay [GIF], se asume texto plano como caption
    return {"type": "text", "caption": contenido}

# /editar_encabezado Texto nuevo del encabezado
async def editar_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    autorizados = cargar_autorizados()

    if user_id not in autorizados:
        await update.message.reply_text("No estás autorizada para usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Uso correcto: /editar_encabezado Texto nuevo del encabezado")
        return

    nuevo_encabezado = " ".join(context.args).strip()

    with open(ENCABEZADO_FILE, "w", encoding="utf-8") as f:
        f.write(nuevo_encabezado)

    await update.message.reply_text("✅ Encabezado actualizado correctamente.")

# /estado - Ver resumen del bot
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in cargar_autorizados():
        await update.message.reply_text("No estás autorizado para usar este comando.")
        return

    total_canales = 0
    fijos = ["SOBRENATURAL", "ADD MY CHANNEL"]
    canales_fijos = 0

    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales = json.load(f)
            total_canales = len(canales)
            canales_fijos = sum(1 for c in canales if any(f in c["nombre"] for f in fijos))

    total_autorizados = len(cargar_autorizados())

    from pytz import timezone
    from datetime import datetime
    tz = timezone("US/Eastern")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    proxima = "No programado"
    job = scheduler.get_job("botonera_diaria")
    if job and job.next_run_time:
        proxima = job.next_run_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

    texto = (
        f"🧠 *Estado del bot:*\n\n"
        f"• Fecha actual: `{now}`\n"
        f"• Canales totales: `{total_canales}`\n"
        f"• Canales fijos: `{canales_fijos}`\n"
        f"• Autorizados: `{total_autorizados}`\n"
        f"• Próxima publicación: `{proxima}`"
    )

    await update.message.reply_text(texto, parse_mode="Markdown")
    
    # /ver_encabezado con rastreo
async def ver_encabezado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("✅ Comando recibido... verificando permisos.")
        user_id = update.effective_user.id
        autorizados = cargar_autorizados()

        if user_id not in autorizados:
            await update.message.reply_text("❌ No estás autorizada para usar este comando.")
            return

        await update.message.reply_text("🔍 Leyendo encabezado...")
        encabezado_actual = obtener_encabezado()

        if encabezado_actual.get("type") == "gif" and encabezado_actual.get("file_id"):
            await update.message.reply_text("📤 Enviando encabezado como GIF...")
            await context.bot.send_animation(
    chat_id=update.effective_chat.id,
    animation=encabezado_actual["file_id"],
    caption=f"*Encabezado actual (GIF)*\n\n{encabezado_actual.get('caption', '')}",
    parse_mode="Markdown"
)
        else:
            await update.message.reply_text("📝 Enviando encabezado como texto...")
            texto = f"*Encabezado actual (Texto)*:\n\n{encabezado_actual.get('caption', encabezado_actual)}"
            await update.message.reply_text(texto, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en /ver_encabezado: {e}")

# ✅ Callbacks
app.add_handler(CallbackQueryHandler(callback_eliminar))

# ✅ Reenvíos privados
app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, reenviado_handler))

# ✅ Ejecutar notificación automática al iniciar el bot
app.post_init = notificar_programacion

# ✅ Registro de comandos
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("autorizar", autorizar))
app.add_handler(CommandHandler("revocar", revocar))
app.add_handler(CommandHandler("listar_autorizados", listar_autorizados))
app.add_handler(CommandHandler("agregar", agregar))
app.add_handler(CommandHandler("eliminar", eliminar))
app.add_handler(CommandHandler("botonera", botonera))
app.add_handler(CommandHandler("test_botonera", test_botonera))
app.add_handler(CommandHandler("editar_encabezado", editar_encabezado))
app.add_handler(CommandHandler("ver_encabezado", ver_encabezado))
app.add_handler(CommandHandler("borrar_botonera", borrar_botonera))
app.add_handler(CommandHandler("fileid", fileid))
app.add_handler(CommandHandler("estado", estado))
app.add_handler(CommandHandler("ver_blacklist", ver_blacklist))

# ✅ Callback para botones interactivos
app.add_handler(CallbackQueryHandler(callback_eliminar))

# ✅ Manejar reenvíos privados (para auto-agregado de canales)
app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, reenviado_handler))

mensajes_publicados = []

# ✅ Función para cargar encabezado y botones
async def botonera(app):
    encabezado = obtener_encabezado()
    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in canales]
    teclado = InlineKeyboardMarkup(botones)

    global mensajes_publicados
    mensajes_publicados = []

    for canal in canales:
        canal_id = canal.get("id")

        # Excluir canales fijos
        if canal_id and canal_id not in [-1002050701908, -1001920805141]:
            try:
                if encabezado.get("type") == "gif" and encabezado.get("file_id"):
                    msg = await app.bot.send_animation(
                        chat_id=canal_id,
                        animation=encabezado["file_id"],
                        caption=encabezado["caption"],
                        reply_markup=teclado,
                        parse_mode="Markdown"
                    )
                else:
                    msg = await app.bot.send_message(
                        chat_id=canal_id,
                        text=encabezado.get("caption", "Sin contenido"),
                        reply_markup=teclado,
                        parse_mode="Markdown"
                    )

                mensajes_publicados.append((canal_id, msg.message_id))
                print(f"✅ Publicado en canal {canal_id}")

            except Exception as e:
                motivo = str(e)
                print(f"❌ Error en canal {canal_id}: {motivo}")
                await manejar_canal_invalido(canal, app, motivo)

        # Excluir canales fijos
        if canal_id and canal_id not in [-1002050701908, -1001920805141]:
            try:
                if encabezado.get("type") == "gif" and encabezado.get("file_id"):
                    msg = await app.bot.send_animation(
                        chat_id=canal_id,
                        animation=encabezado["file_id"],
                        caption=encabezado["caption"],
                        reply_markup=teclado,
                        parse_mode="Markdown"
                    )
                else:
                    msg = await app.bot.send_message(
                        chat_id=canal_id,
                        text=encabezado.get("caption", encabezado),
                        reply_markup=teclado,
                        parse_mode="Markdown"
                    )

                mensajes_publicados.append((canal_id, msg.message_id))
                print(f"✅ Publicado en canal {canal_id}")

            except Exception as e:
                motivo = str(e)
                print(f"❌ Error en canal {canal_id}: {motivo}")
                await manejar_canal_invalido(canal, app, motivo)

    # Enviar resumen a admins
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"📤 Botonera enviada a {len(mensajes_publicados)} canales.\nHora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            print(f"⚠️ No se pudo notificar al admin {admin_id}: {e}")

    # Borrar la botonera después de 23 horas
    asyncio.create_task(eliminar_botonera_despues())

# ✅ Enviar resumen a los administradores
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"✅ Botonera enviada a {len(mensajes_publicados)} canales.\n🕒 Hora: {datetime.now().strftime('%H:%M:%S')}",
            )
        except Exception as e:
            print(f"❌ No se pudo notificar a admin {admin_id}: {e}")

    asyncio.create_task(eliminar_botonera_despues())

    # Separar los canales fijos
    fijo1 = next((c for c in canales if "SOBRENATURAL" in c["nombre"]), None)
    fijo2 = next((c for c in canales if "ADD MY CHANNEL" in c["nombre"]), None)
    canales = [c for c in canales if c not in [fijo1, fijo2]]

    random.shuffle(canales)
    if fijo1: canales.append(fijo1)
    if fijo2: canales.append(fijo2)

    botones = [[InlineKeyboardButton(c["nombre"], url=c["enlace"])] for c in canales]
    teclado = InlineKeyboardMarkup(botones)
    encabezado = obtener_encabezado()

    asyncio.create_task(eliminar_botonera_despues())

# 🗑️ Eliminación de botonera después de 23 horas
async def eliminar_botonera_despues():
    await asyncio.sleep(82800)  # 23 horas

    exitosos = 0
    fallos = 0

    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales_info = json.load(f)
    else:
        canales_info = []

    for chat_id, msg_id in mensajes_publicados:
        try:
            await app.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            exitosos += 1
            print(f"🗑️ Mensaje eliminado en canal {chat_id}")
        except Exception as e:
            fallos += 1
            print(f"❌ No se pudo eliminar en canal {chat_id}: {e}")

    # Notificación final
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=f"🧹 Botonera eliminada.\n✅ {exitosos} mensajes eliminados\n❌ {fallos} fallos"
            )
        except:
            pass

    # Cargar datos de canales
    canales_info = []
    if os.path.exists(CANAL_ARCHIVO):
        with open(CANAL_ARCHIVO, "r", encoding="utf-8") as f:
            canales_info = json.load(f)

    for chat_id, msg_id in mensajes_publicados:
        try:
            await app.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            print(f"🗑️ Mensaje eliminado en canal {chat_id}")
            exitosos += 1
        except Exception as e:
            motivo = str(e)

            # Buscar datos del canal
            canal = next((c for c in canales_info if c["id"] == chat_id), None)
            nombre = canal["nombre"] if canal else "Desconocido"
            enlace = canal["enlace"] if canal else "No disponible"

            print(f"❌ No se pudo eliminar en {chat_id}: {motivo}")
            fallos.append({
                "id": chat_id,
                "nombre": nombre,
                "enlace": enlace,
                "motivo": motivo
            })

            # ✅ Castigar si el error lo amerita
            motivos_castigables = [
                "message to delete not found",
                "can't be deleted",
                "have no rights",
                "was kicked",
                "not enough rights"
            ]
            castigar = any(m in motivo.lower() for m in motivos_castigables)
            if castigar and canal:
                await manejar_canal_invalido(canal, app, motivo)

    # ✅ Notificar a los administradores
    from datetime import datetime
    total = len(mensajes_publicados)

    mensaje = (
        f"🗑️ Botonera eliminada automáticamente.\n"
        f"✅ Eliminados: {exitosos} de {total} mensajes.\n"
        f"🕒 Hora: {datetime.now().strftime('%H:%M:%S')}\n"
    )

    if fallos:
        mensaje += "\n⚠️ *Errores al eliminar:*\n"
        for f in fallos:
            mensaje += (
                f"• *{f['nombre']}*\n"
                f"  ↪️ [Abrir canal]({f['enlace']})\n"
                f"  🆔 `{f['id']}`\n"
                f"  ❌ _{f['motivo']}_\n\n"
            )

    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=mensaje,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"❌ No se pudo notificar la eliminación a admin {admin_id}: {e}")

# ✅ Iniciar el bot
application.run_polling()