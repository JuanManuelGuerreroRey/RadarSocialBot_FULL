
import os
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GRUPO_ID = -1001169225264

messages = []

# Guardar mensajes
def guardar_datos():
    with open("interacciones.json", "w") as f:
        json.dump(messages, f)

# Cargar mensajes
def cargar_datos():
    global messages
    try:
        with open("interacciones.json", "r") as f:
            messages = json.load(f)
    except:
        messages = []

# Manejo de mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat_id == GRUPO_ID:
        msg = update.message
        text = msg.text or ""

        messages.append({
            "user": msg.from_user.first_name,
            "user_id": msg.from_user.id,
            "text": text,
            "reply_to": msg.reply_to_message.from_user.first_name if msg.reply_to_message else None,
            "timestamp": msg.date.isoformat(),
            "chat_id": msg.chat_id
        })
        guardar_datos()

        # Reacciones automáticas
        lower_text = text.lower()
        if "franco" in lower_text:
            await msg.reply_text("Arriba España 🤚")
        elif "bro" in lower_text:
            await msg.reply_text(random.choice(["Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"]))
        elif "moros" in lower_text:
            await msg.reply_text("Moros no, España no es un zoo.")
        elif "negros" in lower_text:
            await msg.reply_text("No soy racista, soy ordenado. Dios creó los continentes por algo.")
        elif "charo" in lower_text:
            await msg.reply_text(random.choice([
                "Sola y borracha quiero llegar a casa",
                "La culpa es del Hetero- patriarcado",
                "Pedro Sánchez es muy guapo"
            ]))

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Radar Social Bot activo. Usa /help para ver comandos disponibles.")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/interacciones - Ranking global de interacciones entre todos los usuarios
"
        "/pareja_dia - Pareja del día
"
        "/pareja_semana - Pareja de la semana
"
        "/pareja_mes - Pareja del mes
"
        "/resumen - Resumen del grupo (experimental)
"
        "/stats - Top 10 usuarios más activos
"
        "/menciones_juan - Ranking de quién menciona a Juan
"
        "/ranking_menciones - Ranking global de menciones entre usuarios"
    )

# /interacciones
async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if m["reply_to"]:
            par = tuple(sorted([m["user"], m["reply_to"]]))
            conteo[par] += 1
    if conteo:
        texto = "
".join([f"{a} ❤️ {b}: {c}" for (a, b), c in conteo.most_common(10)])
        await update.message.reply_text(f"Interacciones más frecuentes:
{texto}")
    else:
        await update.message.reply_text("No hay interacciones aún.")

# pareja del día/semana/mes
async def pareja_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.utcnow()
    comando = update.message.text[1:]
    if comando == "pareja_dia":
        desde = ahora - timedelta(days=1)
    elif comando == "pareja_semana":
        desde = ahora - timedelta(days=7)
    elif comando == "pareja_mes":
        desde = ahora - timedelta(days=30)
    else:
        await update.message.reply_text("Comando inválido.")
        return

    conteo = Counter()
    for m in messages:
        if m["reply_to"] and datetime.fromisoformat(m["timestamp"]) > desde:
            pareja = tuple(sorted([m["user"], m["reply_to"]]))
            conteo[pareja] += 1

    if conteo:
        (a, b), val = conteo.most_common(1)[0]
        await update.message.reply_text(f"💘 Pareja destacada: {a} y {b} con {val} interacciones.")
    else:
        await update.message.reply_text("No hay suficientes datos.")

# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m["user"] for m in messages)
    texto = "
".join([f"{u}: {c}" for u, c in conteo.most_common(10)])
    await update.message.reply_text(f"Top 10 usuarios más activos:
{texto}")

# /menciones_juan
async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if "juan" in (m["text"] or "").lower():
            conteo[m["user"]] += 1
    if conteo:
        texto = "
".join([f"{u}: {c}" for u, c in conteo.most_common()])
        await update.message.reply_text(f"Menciones a Juan:
{texto}")
    else:
        await update.message.reply_text("Nadie ha mencionado a Juan.")

# /ranking_menciones
async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if m["reply_to"]:
            conteo[(m["user"], m["reply_to"])] += 1
    texto = "
".join([f"{a} → {b}: {c}" for (a, b), c in conteo.most_common(10)])
    await update.message.reply_text("Ranking de menciones entre usuarios:
" + texto)

# Lanzamiento
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("interacciones", interacciones))
    app.add_handler(CommandHandler("pareja_dia", pareja_periodo))
    app.add_handler(CommandHandler("pareja_semana", pareja_periodo))
    app.add_handler(CommandHandler("pareja_mes", pareja_periodo))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))

    app.run_polling()
