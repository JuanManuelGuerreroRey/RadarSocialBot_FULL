import os
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext
)
from asyncio import create_task

TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GRUPO_ID = -1001169225264

messages = []
replies = defaultdict(list)

def guardar_datos():
    with open("interacciones.json", "w") as f:
        json.dump(messages, f)

def cargar_datos():
    global messages
    try:
        with open("interacciones.json", "r") as f:
            messages = json.load(f)
    except:
        messages = []

def contar_interacciones():
    interacciones = defaultdict(int)
    for m in messages:
        if m['reply_to']:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            interacciones[pareja] += 1
    return interacciones

def obtener_pareja_top():
    interacciones = contar_interacciones()
    if interacciones:
        top = max(interacciones.items(), key=lambda x: x[1])
        return top
    return None

# Mensajes automáticos por palabras
def respuesta_automatica(text):
    texto = text.lower()
    if "franco" in texto:
        return "Arriba España 🤚"
    if "bro" in texto:
        return random.choice([
            "Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"
        ])
    if "moros" in texto:
        return "Moros no, España no es un zoo"
    if "negros" in texto:
        return "No soy racista, soy ordenado. Dios creó continentes por algo."
    if "charo" in texto:
        return random.choice([
            "Sola y borracha quiero llegar a casa",
            "La culpa es del heteropatriarcado",
            "Pedro Sánchez es muy guapo"
        ])
    return None

# Comandos
async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = obtener_pareja_top()
    if top:
        await update.message.reply_text(
            f"💘 Pareja del día: {top[0][0]} & {top[0][1]} con {top[1]} interacciones."
        )
    else:
        await update.message.reply_text("No hay suficientes interacciones para determinar pareja.")

async def mensaje_automatico_pareja(context: CallbackContext):
    top = obtener_pareja_top()
    if top:
        await context.bot.send_message(
            chat_id=GRUPO_ID,
            text=f"💘 Pareja del día: {top[0][0]} & {top[0][1]} con {top[1]} interacciones."
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m['user'] for m in messages)
    total = sum(conteo.values())
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
        await update.message.reply_text("Nadie ha mencionado a Juan todavía.")

async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = defaultdict(Counter)
    for m in messages:
        if m['reply_to']:
            ranking[m["user"]][m["reply_to"]] += 1
    resultado = []
    for emisor in ranking:
        for receptor, cantidad in ranking[emisor].items():
            resultado.append((emisor, receptor, cantidad))
    resultado.sort(key=lambda x: x[2], reverse=True)
    texto = "\n".join([f"{a} → {b}: {n} interacciones" for a, b, n in resultado[:15]])
    if texto:
        await update.message.reply_text("🏷 Ranking de menciones e interacciones:\n" + texto)
    else:
        await update.message.reply_text("No hay interacciones registradas aún.")

async def raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Total de mensajes almacenados: {len(messages)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat_id == GRUPO_ID:
        msg = update.message
        texto = msg.text or ""
        messages.append({
            "user": msg.from_user.first_name,
            "user_id": msg.from_user.id,
            "text": texto,
            "reply_to": msg.reply_to_message.from_user.first_name if msg.reply_to_message else None,
            "timestamp": msg.date.isoformat(),
            "chat_id": msg.chat_id
        })
        guardar_datos()

        respuesta = respuesta_automatica(texto)
        if respuesta:
            await update.message.reply_text(respuesta)

# Inicialización
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(CommandHandler("raw", raw))

    # Enviar pareja cada 1 hora
    app.job_queue.run_repeating(mensaje_automatico_pareja, interval=3600, first=10)

    app.run_polling()
