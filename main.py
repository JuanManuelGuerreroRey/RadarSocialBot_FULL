import logging
import json
import os
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ'
GROUP_ID = -1001169225264

# Rutas de almacenamiento
INTERACCIONES_FILE = "interacciones.json"
MENSAJES_FILE = "mensajes.json"

# Carga persistente
def cargar_datos():
    if os.path.exists(INTERACCIONES_FILE):
        with open(INTERACCIONES_FILE, "r") as f:
            interacciones = json.load(f)
    else:
        interacciones = {}

    if os.path.exists(MENSAJES_FILE):
        with open(MENSAJES_FILE, "r") as f:
            mensajes = json.load(f)
    else:
        mensajes = []

    return interacciones, mensajes

interacciones, mensajes = cargar_datos()

# Guardar cambios
def guardar_datos():
    with open(INTERACCIONES_FILE, "w") as f:
        json.dump(interacciones, f)
    with open(MENSAJES_FILE, "w") as f:
        json.dump(mensajes, f)

# Normaliza nombres
def get_username(user):
    return user.get("username") or f'{user["first_name"]}'

# Procesamiento de mensajes
def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    username = get_username(user)
    text = update.message.text or ""

    mensajes.append({
        "usuario": username,
        "mensaje": text,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Contabilizar interacciones por menciones
    for palabra in text.split():
        if palabra.startswith("@"):
            mencionado = palabra[1:]
            if username != mencionado:
                interacciones.setdefault(username, {}).setdefault(mencionado, 0)
                interacciones[username][mencionado] += 1

    # Contabilizar respuestas
    if update.message.reply_to_message:
        reply_user = get_username(update.message.reply_to_message.from_user)
        if username != reply_user:
            interacciones.setdefault(username, {}).setdefault(reply_user, 0)
            interacciones[username][reply_user] += 1

    # Respuestas automáticas
    if "Franco" in text:
        update.message.reply_text("Arriba España 🤚")
    if "bro" in text.lower():
        update.message.reply_text(context.bot_data.setdefault("bro_msg", "Hay niveles bro"))
    if "moros" in text.lower():
        update.message.reply_text("Moros no, España no es un zoo.")
    if "negros" in text.lower():
        update.message.reply_text("No soy racista, soy ordenado. Dios creó continentes por algo.")
    if "charo" in text.lower():
        update.message.reply_text("Sola y borracha quiero llegar a casa.")

    guardar_datos()

# /interacciones
def interacciones_command(update: Update, context: CallbackContext):
    texto = "💬 Interacciones globales:\n"
    for emisor, menciones in interacciones.items():
        for receptor, cantidad in menciones.items():
            texto += f"{emisor} → {receptor}: {cantidad} interacciones\n"
    update.message.reply_text(texto or "No hay interacciones registradas.")

# /stats
def stats_command(update: Update, context: CallbackContext):
    contador = Counter([msg["usuario"] for msg in mensajes])
    texto = "📊 Top usuarios activos:\n"
    for usuario, cantidad in contador.most_common(10):
        texto += f"{usuario}: {cantidad} mensajes\n"
    update.message.reply_text(texto)

# /menciones_juan
def menciones_juan_command(update: Update, context: CallbackContext):
    conteo = Counter()
    for msg in mensajes:
        if "juan" in msg["mensaje"].lower():
            conteo[msg["usuario"]] += 1
    texto = "🗣 Menciones a Juan:\n"
    for usuario, cantidad in conteo.items():
        texto += f"{usuario}: {cantidad} menciones\n"
    update.message.reply_text(texto or "Nadie ha mencionado a Juan aún.")

# /pareja_dia
def pareja_dia_command(update: Update, context: CallbackContext):
    parejas = Counter()
    for emisor, receptores in interacciones.items():
        for receptor, cantidad in receptores.items():
            if emisor != receptor:
                clave = tuple(sorted([emisor, receptor]))
                parejas[clave] += cantidad

    if parejas:
        pareja, total = parejas.most_common(1)[0]
        texto = f"💘😍👉 Pareja del día: {pareja[0]} & {pareja[1]} 👈 ({total} interacciones)"
    else:
        texto = "Aún no hay suficientes interacciones para formar pareja del día."

    update.message.reply_text(texto)

# /resumen (modo simple por ahora)
def resumen_command(update: Update, context: CallbackContext):
    if len(mensajes) < 10:
        update.message.reply_text("No hay suficientes mensajes para generar un resumen aún.")
        return

    temas = Counter()
    for msg in mensajes[-100:]:
        for palabra in msg["mensaje"].lower().split():
            if palabra not in ["el", "la", "y", "de", "que", "en", "a", "los"]:
                temas[palabra] += 1

    top = temas.most_common(5)
    texto = "🧠 Resumen (simplificado):\nTemas destacados:\n"
    for palabra, count in top:
        texto += f"• {palabra} ({count})\n"
    update.message.reply_text(texto)

# Comandos
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 RadarSocialBot activo. Usa /interacciones, /stats, /pareja_dia, /resumen...")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("interacciones", interacciones_command))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("menciones_juan", menciones_juan_command))
    dp.add_handler(CommandHandler("pareja_dia", pareja_dia_command))
    dp.add_handler(CommandHandler("resumen", resumen_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.group, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
