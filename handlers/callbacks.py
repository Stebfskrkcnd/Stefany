from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.helpers import load_json, save_json

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    data = query.data
    if not data:
        return
    canales = load_json("data/channels.json")

    if data.startswith("toggle:"):
        canal_id = int(data.split(":")[1])
        canales = [c for c in canales if c["id"] != canal_id]  # 🔥 elimina completamente el canal
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