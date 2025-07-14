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
resumen_buffer = []
ultima_pareja_dia = datetime.utcnow() - timedelta(hours=24)

# Guardar mensajes
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

# Auto respuestas por palabras clave
AUTO_RESPUESTAS = {
    "franco": ["Arriba España 🤚"],
    "bro": ["Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"],
    "moros": ["Moros no, españa no es un zoo."],
    "negros": ["No soy racista, soy ordenado. Dios creó el mundo en diversos continentes, por algo será."],
    "charo": ["Sola y borracha quiero llegar a casa", "La culpa es del Hetero-patriarcado", "Pedro Sánchez es muy guapo"]
}

# Manejador de mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resumen_buffer, ultima_pareja_dia
    if update.message and update.message.chat_id == GRUPO_ID:
        msg = update.message
        texto = msg.text.lower()

        # Guardar mensaje
        messages.append({
            "user": msg.from_user.first_name,
            "user_id": msg.from_user.id,
            "text": msg.text,
            "reply_to": msg.reply_to_message.from_user.first_name if msg.reply_to_message else None,
            "timestamp": msg.date.isoformat(),
            "chat_id": msg.chat_id
        })
        resumen_buffer.append(msg.text)
        guardar_datos()

        # Auto respuestas
        for palabra, respuestas in AUTO_RESPUESTAS.items():
            if palabra in texto:
                respuesta = random.choice(respuestas)
                await msg.reply_text(respuesta)
                break

        # Cada 400 mensajes anunciar pareja del día
        if len(messages) % 400 == 0 and datetime.utcnow() - ultima_pareja_dia > timedelta(hours=12):
            await pareja_automatica(context)
            ultima_pareja_dia = datetime.utcnow()

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo. Usa /help para ver comandos.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/interacciones - Ranking global de interacciones entre todos los usuarios\n"
        "/pareja_dia - Pareja con más interacción del día\n"
        "/pareja_semana - Pareja con más interacción de los últimos 7 días\n"
        "/pareja_mes - Pareja con más interacción del mes\n"
        "/resumen - Resumen breve del día\n"
        "/stats - Top 10 usuarios más activos\n"
        "/menciones_juan - Quién menciona más a Juan\n"
        "/ranking_menciones - Quién menciona a quién"
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumen_texto = "".join(resumen_buffer[-300:])
    resumen_generado = f"Resumen generado. Temas frecuentes: {', '.join(set(p for p in resumen_texto.split() if len(p) > 6)[:5])}"
    await update.message.reply_text(resumen_generado)

async def pareja_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text
    ahora = datetime.utcnow()
    dias = {"/pareja_dia": 1, "/pareja_semana": 7, "/pareja_mes": 30}.get(comando, 1)
    desde = ahora - timedelta(days=dias)

    interacciones = Counter()
    for m in messages:
        if m['reply_to'] and datetime.fromisoformat(m['timestamp']) > desde:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            interacciones[pareja] += 1

    if interacciones:
        top = interacciones.most_common(1)[0]
        await update.message.reply_text(f"💘 Pareja destacada: {top[0][0]} y {top[0][1]} con {top[1]} interacciones.")
    else:
        await update.message.reply_text("No hay suficientes interacciones para determinar pareja.")

async def pareja_automatica(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.utcnow()
    desde = ahora - timedelta(days=1)
    interacciones = Counter()
    for m in messages:
        if m['reply_to'] and datetime.fromisoformat(m['timestamp']) > desde:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            interacciones[pareja] += 1
    if interacciones:
        top = interacciones.most_common(1)[0]
        await context.bot.send_message(chat_id=GRUPO_ID, text=f"💘 Pareja del día: 👉 {top[0][0]} & {top[0][1]} 👈")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m['user'] for m in messages)
    top = conteo.most_common(10)
    texto = "\n".join([f"{u}: {c} mensajes" for u, c in top])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{texto}")

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menciones = Counter()
    for m in messages:
        if "juan" in m["text"].lower():
            menciones[m["user"]] += 1
    texto = "\n".join([f"{u}: {c} menciones" for u, c in menciones.most_common(5)])
    await update.message.reply_text(f"🔍 Menciones a Juan:\n{texto}")

async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menciones = Counter()
    for m in messages:
        if m['reply_to']:
            pareja = (m['user'], m['reply_to'])
            menciones[pareja] += 1
    top = menciones.most_common(10)
    texto = "\n".join([f"{p[0]} → {p[1]}: {c} interacciones" for p, c in top])
    await update.message.reply_text(f"📈 Ranking de menciones entre usuarios:\n{texto}")

async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tabla = defaultdict(lambda: defaultdict(int))
    for m in messages:
        if m['reply_to']:
            tabla[m['user']][m['reply_to']] += 1

    texto = ""
    for u1 in tabla:
        for u2 in tabla[u1]:
            texto += f"{u1} → {u2}: {tabla[u1][u2]} veces\n"
    await update.message.reply_text(f"📊 Interacciones globales:\n{texto[:4000]}")

# Lanzar bot
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("pareja_dia", pareja_periodo))
    app.add_handler(CommandHandler("pareja_semana", pareja_periodo))
    app.add_handler(CommandHandler("pareja_mes", pareja_periodo))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(CommandHandler("interacciones", interacciones))

    app.run_polling()
