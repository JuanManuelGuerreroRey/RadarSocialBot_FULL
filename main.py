import os
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
GRUPO_ID = int(os.getenv("GRUPO_ID"))

messages = []
replies = defaultdict(list)
menciones = defaultdict(Counter)

def guardar_datos():
    with open("interacciones.json", "w") as f:
        json.dump(messages, f)

def cargar_datos():
    global messages
    try:
        with open("interacciones.json", "r") as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

def analizar_interacciones():
    conteo = Counter()
    for m in messages:
        if m['reply_to']:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            conteo[pareja] += 1
    return conteo

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat_id == GRUPO_ID:
        msg = update.message
        user = msg.from_user.first_name
        user_id = msg.from_user.id
        text = msg.text or ""
        reply_to = msg.reply_to_message.from_user.first_name if msg.reply_to_message else None
        timestamp = msg.date.isoformat()

        messages.append({
            "user": user,
            "user_id": user_id,
            "text": text,
            "reply_to": reply_to,
            "timestamp": timestamp,
            "chat_id": msg.chat_id
        })

        if reply_to:
            menciones[user][reply_to] += 1

        guardar_datos()

        if "franco" in text.lower():
            await msg.reply_text("Arriba España 🤚")
        if "moros" in text.lower():
            await msg.reply_text("Moros no, España no es un zoo.")
        if "negros" in text.lower():
            await msg.reply_text("No soy racista, soy ordenado.")
        if "charo" in text.lower():
            await msg.reply_text(random.choice([
                "Sola y borracha quiero llegar a casa",
                "La culpa es del Heteropatriarcado",
                "Pedro Sánchez es muy guapo"
            ]))
        if "bro" in text.lower():
            await msg.reply_text(random.choice([
                "Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"
            ]))

# COMANDOS

async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.utcnow()
    desde = ahora - timedelta(days=1)
    interacciones = Counter()
    for m in messages:
        if m['reply_to']:
            fecha = datetime.fromisoformat(m['timestamp'])
            if fecha > desde:
                pareja = tuple(sorted([m['user'], m['reply_to']]))
                interacciones[pareja] += 1
    if interacciones:
        top = interacciones.most_common(1)[0]
        await update.message.reply_text(f"💘 Pareja del día: {top[0][0]} y {top[0][1]} ({top[1]} interacciones)")
    else:
        await update.message.reply_text("No hay suficientes interacciones aún.")

async def pareja_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text[1:]
    ahora = datetime.utcnow()
    if comando == "pareja_semana":
        desde = ahora - timedelta(days=7)
    elif comando == "pareja_mes":
        desde = ahora - timedelta(days=30)
    else:
        return

    interacciones = Counter()
    for m in messages:
        if m['reply_to']:
            fecha = datetime.fromisoformat(m['timestamp'])
            if fecha > desde:
                pareja = tuple(sorted([m['user'], m['reply_to']]))
                interacciones[pareja] += 1
    if interacciones:
        top = interacciones.most_common(1)[0]
        await update.message.reply_text(f"💘 Pareja destacada ({comando[7:]}): {top[0][0]} y {top[0][1]} ({top[1]} interacciones)")
    else:
        await update.message.reply_text("No hay suficientes interacciones.")

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    textos = [m["text"] for m in messages[-300:] if m["text"]]
    if not textos:
        await update.message.reply_text("No hay suficientes mensajes para generar un resumen.")
        return
    temas = Counter()
    for texto in textos:
        for palabra in texto.split():
            if palabra.lower() not in ["el", "la", "de", "y", "que", "en", "a", "los", "por", "se"]:
                temas[palabra.lower()] += 1
    top = temas.most_common(5)
    resumen = ", ".join([f"{p[0]} ({p[1]})" for p in top])
    await update.message.reply_text(f"🧠 Resumen de temas: {resumen}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m['user'] for m in messages)
    top = conteo.most_common(10)
    texto = "\n".join([f"{u}: {c} mensajes" for u, c in top])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{texto}")

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if "juan" in m["text"].lower():
            conteo[m["user"]] += 1
    if conteo:
        texto = "\n".join([f"{u}: {c} menciones a Juan" for u, c in conteo.most_common()])
        await update.message.reply_text(f"📣 Menciones a Juan:\n{texto}")
    else:
        await update.message.reply_text("Nadie ha mencionado a Juan.")

async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = []
    for emisor, receptores in menciones.items():
        for receptor, count in receptores.items():
            resultado.append((emisor, receptor, count))
    resultado.sort(key=lambda x: x[2], reverse=True)
    if not resultado:
        await update.message.reply_text("No hay menciones registradas.")
        return
    texto = "\n".join([f"{e} menciona a {r}: {c} veces" for e, r, c in resultado[:10]])
    await update.message.reply_text(f"🏷️ Ranking de menciones:\n{texto}")

async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interacciones = analizar_interacciones()
    if not interacciones:
        await update.message.reply_text("No hay interacciones registradas.")
        return
    top = interacciones.most_common(10)
    texto = "\n".join([f"{a} 🤝 {b}: {c}" for (a, b), c in top])
    await update.message.reply_text(f"📈 Interacciones:\n{texto}")

# MAIN
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(CommandHandler("pareja_semana", pareja_periodo))
    app.add_handler(CommandHandler("pareja_mes", pareja_periodo))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(CommandHandler("interacciones", interacciones))

    app.run_polling()
