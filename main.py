import os
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from asyncio import create_task

TOKEN = "TU_TOKEN_AQUI"
GRUPO_ID = -1001169225264

messages = []
replies = defaultdict(list)
mentions = defaultdict(list)

# ──── COMANDOS ────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    counter = Counter(msg['user'] for msg in messages)
    top = counter.most_common(10)
    text = "📊 Top usuarios activos:\n" + "\n".join(f"{u}: {c} mensajes" for u, c in top)
    await update.message.reply_text(text)

async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair_counts = Counter()
    for msg in messages:
        for reply_to in msg.get("replied_to", []):
            pair = (msg["user"], reply_to)
            pair_counts[pair] += 1
    texto = "💬 Interacciones globales:\n"
    for (a, b), c in pair_counts.most_common(10):
        texto += f"{a} → {b}: {c} interacciones\n"
    await update.message.reply_text(texto)

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    juan_mentions = Counter()
    for msg in messages:
        if 'juan' in msg['text'].lower():
            juan_mentions[msg['user']] += 1
    if not juan_mentions:
        await update.message.reply_text("Nadie ha mencionado a Juan aún.")
    else:
        text = "📰 Menciones a Juan:\n" + "\n".join(f"{u}: {c} menciones" for u, c in juan_mentions.items())
        await update.message.reply_text(text)

async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(calcular_pareja_dia())

# ──── PAREJA AUTOMÁTICA ────

def calcular_pareja_dia():
    counter = Counter()
    for msg in messages:
        for replied in msg.get("replied_to", []):
            counter[(msg["user"], replied)] += 1
        for mention in msg.get("mentions", []):
            counter[(msg["user"], mention)] += 1
    if not counter:
        return "Aún no hay suficientes interacciones para determinar la pareja del día."
    (user1, user2), total = counter.most_common(1)[0]
    return f"💘 La pareja del día es: {user1} 💞 {user2} con {total} interacciones"

async def mensaje_automatico_pareja(context: ContextTypes.DEFAULT_TYPE):
    text = calcular_pareja_dia()
    await context.bot.send_message(chat_id=GRUPO_ID, text=text)

# ──── MANEJO DE MENSAJES ────

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    usuario = msg.from_user.full_name
    texto = msg.text or ""

    menciones_en_msg = [e.user.full_name for e in msg.entities if e.type == "mention"] if msg.entities else []

    info_msg = {
        "user": usuario,
        "text": texto,
        "mentions": [],
        "replied_to": []
    }

    if msg.reply_to_message:
        info_msg["replied_to"].append(msg.reply_to_message.from_user.full_name)

    if "juan" in texto.lower():
        info_msg["mentions"].append("Juan")

    messages.append(info_msg)

    if any(word in texto.lower() for word in ["franco", "pro", "facha", "comunista"]):
        await msg.reply_text("🧠 Mensaje detectado con contenido político.")

# ──── MAIN ────

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("interacciones", interacciones))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), manejar_mensaje))

    # TAREA AUTOMÁTICA CADA HORA
    app.job_queue.run_repeating(mensaje_automatico_pareja, interval=3600, first=10)

    print("Bot corriendo...")
    app.run_polling()
