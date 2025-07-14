import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
import random

TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GRUPO_ID = -1001169225264

messages = []
replies = defaultdict(list)

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

# Manejador de mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat_id == GRUPO_ID:
        msg = update.message
        user = msg.from_user.first_name
        text = msg.text or ""

        messages.append({
            "user": user,
            "user_id": msg.from_user.id,
            "text": text,
            "reply_to": msg.reply_to_message.from_user.first_name if msg.reply_to_message else None,
            "timestamp": msg.date.isoformat(),
        })
        guardar_datos()

        # Reacciones automáticas
        texto = text.lower()
        if "franco" in texto:
            await msg.reply_text("Arriba España 🤚")
        elif "bro" in texto:
            await msg.reply_text(random.choice(["Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"]))
        elif "moros" in texto:
            await msg.reply_text("Moros no, España no es un zoo.")
        elif "negros" in texto:
            await msg.reply_text("No soy racista, soy ordenado. Dios creó el mundo en diversos continentes, por algo será.")
        elif "charo" in texto:
            await msg.reply_text(random.choice(["Sola y borracha quiero llegar a casa", "La culpa es del heteropatriarcado", "Pedro Sánchez es muy guapo."]))

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Radar Social Bot activado.")

# Comando /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m['user'] for m in messages)
    total = sum(conteo.values())
    top = conteo.most_common(10)
    texto = "\n".join([f"{u}: {c} mensajes" for u, c in top])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{texto}")

# Comando /menciones_juan
async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if "juan" in (m["text"] or "").lower():
            conteo[m["user"]] += 1
    if conteo:
        texto = "\n".join([f"{u}: {c} menciones" for u, c in conteo.most_common()])
        await update.message.reply_text(f"📣 Menciones a Juan:\n{texto}")
    else:
        await update.message.reply_text("Nadie ha mencionado a Juan.")

# Comando /ranking_menciones
async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menciones = Counter()
    for m in messages:
        if m["reply_to"]:
            par = (m["user"], m["reply_to"])
            menciones[par] += 1
    if menciones:
        top = menciones.most_common(10)
        texto = "\n".join([f"{a} ➡️ {b}: {c} interacciones" for (a, b), c in top])
        await update.message.reply_text(f"📈 Ranking menciones:\n{texto}")
    else:
        await update.message.reply_text("No hay interacciones aún.")

# Comando /interacciones
async def interacciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tabla = defaultdict(lambda: defaultdict(int))
    for m in messages:
        if m["reply_to"]:
            tabla[m["user"]][m["reply_to"]] += 1
    texto = ""
    for u in tabla:
        for t in tabla[u]:
            texto += f"{u} ➡️ {t}: {tabla[u][t]}\n"
    await update.message.reply_text(f"📊 Interacciones globales:\n{texto[:4096]}")

# Comando /pareja_dia
async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.utcnow()
    desde = ahora - timedelta(days=1)
    parejas = Counter()
    for m in messages:
        if m['reply_to'] and datetime.fromisoformat(m['timestamp']) > desde:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            parejas[pareja] += 1
    if parejas:
        top = parejas.most_common(1)[0]
        await update.message.reply_text(f"💘 Pareja del día: {top[0][0]} & {top[0][1]} ({top[1]} interacciones)")
    else:
        await update.message.reply_text("No hay suficientes interacciones hoy.")

# /pareja_semana y /pareja_mes
async def pareja_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.utcnow()
    if "semana" in update.message.text:
        desde = ahora - timedelta(days=7)
    elif "mes" in update.message.text:
        desde = ahora - timedelta(days=30)
    else:
        await update.message.reply_text("Comando no reconocido.")
        return
    parejas = Counter()
    for m in messages:
        if m['reply_to'] and datetime.fromisoformat(m['timestamp']) > desde:
            pareja = tuple(sorted([m['user'], m['reply_to']]))
            parejas[pareja] += 1
    if parejas:
        top = parejas.most_common(1)[0]
        await update.message.reply_text(f"💞 Pareja destacada: {top[0][0]} & {top[0][1]} ({top[1]} interacciones)")
    else:
        await update.message.reply_text("No hay suficientes interacciones.")

# Comando /resumen
async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(messages) < 300:
        await update.message.reply_text("Aún no hay suficientes mensajes para generar un resumen.")
        return
    resumen_texto = "Resumen de los temas tratados:\n"
    temas = Counter()
    for m in messages[-300:]:
        palabras = [p.lower() for p in (m['text'] or "").split() if len(p) > 4]
        temas.update(palabras)
    top_temas = temas.most_common(5)
    for palabra, cantidad in top_temas:
        resumen_texto += f"- {palabra} ({cantidad} menciones)\n"
    await update.message.reply_text(resumen_texto)

# Arrancar el bot
if __name__ == "__main__":
    cargar_datos()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(CommandHandler("interacciones", interacciones))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(CommandHandler("pareja_semana", pareja_periodo))
    app.add_handler(CommandHandler("pareja_mes", pareja_periodo))
    app.add_handler(CommandHandler("resumen", resumen))

    app.run_polling()
