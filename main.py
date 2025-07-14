# RadarSocialBot - Versión de prueba

import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from collections import defaultdict
import datetime

# Token e ID del grupo
TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GROUP_ID = -1001169225264

# Diccionarios y contadores
usuarios_activos = defaultdict(int)
menciones_juan = defaultdict(int)
interacciones = defaultdict(lambda: defaultdict(int))
mensajes_guardados = []

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Funciones de comandos ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot activo y funcionando correctamente.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    ranking = sorted(usuarios_activos.items(), key=lambda x: x[1], reverse=True)[:10]
    respuesta = "📊 Top usuarios activos:\n"
    for user, count in ranking:
        respuesta += f"{user}: {count} mensajes\n"
    await update.message.reply_text(respuesta)

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    if not menciones_juan:
        await update.message.reply_text("Nadie ha mencionado a Juan aún.")
        return
    respuesta = "📰 Menciones a Juan:\n"
    for user, count in menciones_juan.items():
        respuesta += f"{user}: {count} menciones\n"
    await update.message.reply_text(respuesta)

async def interacciones_globales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    respuesta = "💬 Interacciones globales:\n"
    for user1, targets in interacciones.items():
        for user2, count in targets.items():
            respuesta += f"{user1} → {user2}: {count} interacciones\n"
    await update.message.reply_text(respuesta)

# Puedes añadir aquí las funciones de pareja del día, resumen, etc.

# --- Manejador de mensajes ---
async def registrar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    autor = update.effective_user.full_name
    texto = update.message.text or ""

    usuarios_activos[autor] += 1
    mensajes_guardados.append(texto)

    # Menciones directas a Juan
    if "juan" in texto.lower():
        menciones_juan[autor] += 1

    # Interacciones por respuesta
    if update.message.reply_to_message:
        receptor = update.message.reply_to_message.from_user.full_name
        interacciones[autor][receptor] += 1

    # Reacciones automáticas por palabras clave
    respuestas = {
        "franco": "Arriba España 🤚",
        "bro": ["Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"],
        "moros": "Moros no, España no es un zoo.",
        "negros": "No soy racista, soy ordenado. Dios creó el mundo en continentes, por algo será.",
        "charo": [
            "Sola y borracha quiero llegar a casa",
            "La culpa es del heteropatriarcado",
            "Pedro Sánchez es muy guapo"
        ]
    }

    for palabra, respuesta in respuestas.items():
        if palabra in texto.lower():
            if isinstance(respuesta, list):
                import random
                await update.message.reply_text(random.choice(respuesta))
            else:
                await update.message.reply_text(respuesta)

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("interacciones", interacciones_globales))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_mensaje))

    print("Bot en funcionamiento")
    app.run_polling()
