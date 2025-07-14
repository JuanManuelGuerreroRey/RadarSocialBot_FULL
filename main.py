import os
import json
import random
from datetime import datetime
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from asyncio import create_task

# Carga variables
TOKEN = os.getenv("BOT_TOKEN")
GRUPO_ID = int(os.getenv("GRUPO_ID", "-1001169225264"))

# Datos en memoria
messages = []
replies = defaultdict(list)
mentions = defaultdict(Counter)

# Guardar y cargar mensajes para evitar pérdida tras reinicio
DATA_FILE = "mensajes.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)

def guardar_datos():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f)

# --- COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola, soy el RadarSocialBot 📡")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = Counter(msg['usuario'] for msg in messages)
    ranking = '\n'.join([f"{user}: {count} mensajes" for user, count in usuarios.most_common(10)])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{ranking}")

async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultados = defaultdict(Counter)
    for r in replies:
        for mencionado in replies[r]:
            resultados[r][mencionado] += 1
    respuesta = "🔁 Interacciones globales:\n"
    for r, cuentas in resultados.items():
        for m, n in cuentas.items():
            respuesta += f"{r} → {m}: {n} interacciones\n"
    await update.message.reply_text(respuesta)

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = Counter()
    for msg in messages:
        if "juan" in msg['texto'].lower():
            resultado[msg['usuario']] += 1
    if resultado:
        texto = '\n'.join([f"{user}: {count} menciones" for user, count in resultado.items()])
        await update.message.reply_text(f"📰 Menciones a Juan:\n{texto}")
    else:
        await update.message.reply_text("Nadie ha mencionado a Juan aún.")

async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interacciones = defaultdict(int)
    for r, lista in replies.items():
        for m in lista:
            pareja = tuple(sorted((r, m)))
            interacciones[pareja] += 1
    if interacciones:
        pareja, _ = max(interacciones.items(), key=lambda x: x[1])
        await update.message.reply_text(f"💞 Pareja del día: {pareja[0]} 💘 {pareja[1]}")
    else:
        await update.message.reply_text("Aún no hay suficientes interacciones.")

async def mensaje_automatico_pareja(context: ContextTypes.DEFAULT_TYPE):
    chat_id = GRUPO_ID
    interacciones = defaultdict(int)
    for r, lista in replies.items():
        for m in lista:
            pareja = tuple(sorted((r, m)))
            interacciones[pareja] += 1
    if interacciones:
        pareja, _ = max(interacciones.items(), key=lambda x: x[1])
        texto = f"💞 Pareja del día: {pareja[0]} 💘 {pareja[1]}"
        await context.bot.send_message(chat_id=chat_id, text=texto)

# --- MENSAJES ---

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.full_name
    texto = update.message.text
    messages.append({'usuario': user, 'texto': texto})
    guardar_datos()

    # Guardar menciones
    if update.message.reply_to_message:
        original = update.message.reply_to_message.from_user.full_name
        replies[user].append(original)

    # Respuestas automáticas
    palabras_clave = ["Franco", "pro", "vox"]
    respuestas = ["¿Estás seguro de eso?", "Interesante punto...", "¿Puedes desarrollar más?"]
    if any(palabra.lower() in texto.lower() for palabra in palabras_clave):
        await update.message.reply_text(random.choice(respuestas))

# --- MAIN APP ---

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("interacciones", interacciones))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), mensaje))

    # Mensaje automático cada hora
    app.job_queue.run_repeating(mensaje_automatico_pareja, interval=3600, first=30)

    app.run_polling()

if __name__ == "__main__":
    main()
