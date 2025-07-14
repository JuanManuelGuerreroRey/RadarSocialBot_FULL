import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GRUPO_ID = -1001169225264

messages = []
replies = defaultdict(list)
contador_mensajes = 0

# Cargar mensajes anteriores si existen
def cargar_datos():
    global messages
    if os.path.exists("interacciones.json"):
        with open("interacciones.json", "r") as f:
            messages = json.load(f)
    else:
        messages = []

# Guardar mensajes nuevos
def guardar_datos():
    with open("interacciones.json", "w") as f:
        json.dump(messages, f)

# -------------------- COMANDOS -----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot activo y funcionando correctamente.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Comandos disponibles:\n"
        "/interacciones - Ranking de interacciones\n"
        "/pareja_dia - Pareja del día\n"
        "/pareja_semana - Pareja de la semana\n"
        "/pareja_mes - Pareja del mes\n"
        "/resumen - Resumen del día\n"
        "/stats - Top usuarios por mensajes\n"
        "/menciones_juan - Quién menciona más a Juan\n"
        "/ranking_menciones - Quién menciona a quién"
    )

# Registrar mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global contador_mensajes
    msg = update.message
    if msg.chat_id == GRUPO_ID:
        contador_mensajes += 1
        messages.append({
            "user": msg.from_user.first_name,
            "user_id": msg.from_user.id,
            "text": msg.text,
            "reply_to": msg.reply_to_message.from_user.first_name if msg.reply_to_message else None,
            "timestamp": msg.date.isoformat()
        })
        guardar_datos()

        # Triggers automáticos
        if "Franco" in msg.text:
            await msg.reply_text("Arriba España 🤚")
        if "moros" in msg.text:
            await msg.reply_text("Moros no, España no es un zoo.")
        if "negros" in msg.text:
            await msg.reply_text("No soy racista, soy ordenado...")
        if "charo" in msg.text:
            await msg.reply_text(random.choice([
                "Sola y borracha quiero llegar a casa",
                "La culpa es del heteropatriarcado",
                "Pedro Sánchez es muy guapo"
            ]))
        if "bro" in msg.text.lower():
            await msg.reply_text(random.choice([
                "Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"
            ]))

        # Lanzar pareja del día cada 400 mensajes
        if contador_mensajes % 400 == 0:
            await pareja_periodo(update, context, modo="dia", auto=True)

# Pareja del día / semana / mes
async def pareja_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE, modo=None, auto=False):
    now = datetime.utcnow()
    if not modo:
        modo = update.message.text.replace("/", "")
    dias = {"dia": 1, "semana": 7, "mes": 30}
    desde = now - timedelta(days=dias.get(modo, 1))
    interacciones = Counter()

    for m in messages:
        fecha = datetime.fromisoformat(m['timestamp'])
        if fecha > desde and m['reply_to']:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            interacciones[pareja] += 1

    if interacciones:
        top = interacciones.most_common(1)[0]
        texto = f"💘 Pareja del {modo}: {top[0][0]} & {top[0][1]} con {top[1]} interacciones."
    else:
        texto = "No hay suficientes interacciones todavía."

    if auto:
        await context.bot.send_message(chat_id=GRUPO_ID, text=texto)
    else:
        await update.message.reply_text(texto)

# Interacciones globales
async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if m['reply_to']:
            key = f"{m['user']} ➡️ {m['reply_to']}"
            conteo[key] += 1
    if conteo:
        ranking = "\n".join([f"{k}: {v}" for k, v in conteo.most_common(20)])
        await update.message.reply_text(f"📊 Interacciones:\n{ranking}")
    else:
        await update.message.reply_text("Aún no hay interacciones registradas.")

# Stats de usuarios
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m['user'] for m in messages)
    ranking = "\n".join([f"{u}: {c} mensajes" for u, c in conteo.most_common(10)])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{ranking}")

# Menciones a Juan
async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if "juan" in m["text"].lower():
            conteo[m["user"]] += 1
    if conteo:
        ranking = "\n".join([f"{u}: {c} menciones" for u, c in conteo.most_common()])
        await update.message.reply_text(f"🔍 Menciones a Juan:\n{ranking}")
    else:
        await update.message.reply_text("Nadie ha mencionado a Juan aún.")

# Ranking menciones generales
async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if m['reply_to']:
            key = f"{m['user']} ➡️ {m['reply_to']}"
            conteo[key] += 1
    if conteo:
        top = "\n".join([f"{k}: {v} veces" for k, v in conteo.most_common(10)])
        await update.message.reply_text(f"📈 Ranking menciones:\n{top}")
    else:
        await update.message.reply_text("Aún no hay suficientes menciones.")

# -------------------- MAIN -----------------------
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("pareja_dia", lambda u, c: pareja_periodo(u, c, "dia")))
    app.add_handler(CommandHandler("pareja_semana", lambda u, c: pareja_periodo(u, c, "semana")))
    app.add_handler(CommandHandler("pareja_mes", lambda u, c: pareja_periodo(u, c, "mes")))
    app.add_handler(CommandHandler("interacciones", interacciones))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
