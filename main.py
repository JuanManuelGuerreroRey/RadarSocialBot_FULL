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
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import nltk

nltk.download("punkt")

# Configuración
TOKEN = "8147087924:AAH-U9f5_vK1cpH1-kYqFHRjQacuLouvXVQ"
GRUPO_ID = -1001169225264

messages = []
interacciones = defaultdict(lambda: defaultdict(int))
mensajes_para_resumen = []
resumen_counter = 0
pareja_counter = 0

# Guardar mensajes
def guardar():
    with open("mensajes.json", "w") as f:
        json.dump(messages, f)

# Cargar mensajes
def cargar():
    global messages
    try:
        with open("mensajes.json", "r") as f:
            messages = json.load(f)
    except:
        messages = []

# Manejador de texto
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resumen_counter, pareja_counter
    msg = update.message
    if msg.chat_id != GRUPO_ID or not msg.text:
        return

    user = msg.from_user.first_name
    reply_to = msg.reply_to_message.from_user.first_name if msg.reply_to_message else None
    text = msg.text.strip()

    messages.append({
        "user": user,
        "text": text,
        "reply_to": reply_to,
        "timestamp": msg.date.isoformat()
    })

    mensajes_para_resumen.append(text)
    resumen_counter += 1
    pareja_counter += 1

    if reply_to:
        interacciones[user][reply_to] += 1

    if "franco" in text.lower():
        await msg.reply_text("Arriba España 🤚")
    if "bro" in text.lower():
        await msg.reply_text(random.choice(["Masivo bro", "Siempre ganando", "Hay niveles bro", "Fucking panzas"]))
    if "moros" in text.lower():
        await msg.reply_text("Moros no, España no es un zoo.")
    if "negros" in text.lower():
        await msg.reply_text("No soy racista, soy ordenado. Dios creó el mundo en diversos continentes, por algo será.")
    if "charo" in text.lower():
        await msg.reply_text(random.choice([
            "Sola y borracha quiero llegar a casa",
            "La culpa es del heteropatriarcado",
            "Pedro Sánchez es muy guapo"
        ]))

    # Resumen automático
    if resumen_counter >= 300:
        resumen = generar_resumen("\n".join(mensajes_para_resumen[-300:]))
        await context.bot.send_message(chat_id=GRUPO_ID, text=f"📝 Resumen del grupo:\n{resumen}")
        resumen_counter = 0

    # Pareja automática
    if pareja_counter >= 400:
        pareja = calcular_pareja(1)
        if pareja:
            await context.bot.send_message(chat_id=GRUPO_ID, text=f"💘 Pareja del día: {pareja[0]} & {pareja[1]}")
        pareja_counter = 0

    guardar()

def calcular_pareja(dias):
    ahora = datetime.utcnow()
    desde = ahora - timedelta(days=dias)
    conteo = Counter()
    for m in messages:
        if m["reply_to"]:
            tiempo = datetime.fromisoformat(m["timestamp"])
            if tiempo > desde:
                pareja = tuple(sorted([m["user"], m["reply_to"]]))
                conteo[pareja] += 1
    if conteo:
        return conteo.most_common(1)[0][0]
    return None

def generar_resumen(texto):
    parser = PlaintextParser.from_string(texto, Tokenizer("spanish"))
    summarizer = LexRankSummarizer()
    resumen = summarizer(parser.document, 3)
    return "\n".join(str(s) for s in resumen)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Radar Social Bot está activo.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter(m["user"] for m in messages)
    top = conteo.most_common(10)
    texto = "\n".join([f"{u}: {c} mensajes" for u, c in top])
    await update.message.reply_text(f"📊 Top usuarios activos:\n{texto}")

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumen = generar_resumen("\n".join(m.text for m in messages[-300:] if m.get("text")))
    await update.message.reply_text(f"🧠 Resumen del grupo:\n{resumen}")

async def interacciones_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = []
    for usuario, targets in interacciones.items():
        for objetivo, conteo in targets.items():
            resultado.append((usuario, objetivo, conteo))
    resultado.sort(key=lambda x: -x[2])
    texto = "\n".join([f"{a} → {b}: {n} interacciones" for a, b, n in resultado])
    await update.message.reply_text(f"🔁 Interacciones globales:\n{texto}")

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        if "juan" in m["text"].lower():
            conteo[m["user"]] += 1
    texto = "\n".join([f"{u}: {c} menciones" for u, c in conteo.most_common(10)])
    await update.message.reply_text(f"🧾 Menciones a Juan:\n{texto}")

async def ranking_menciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conteo = Counter()
    for m in messages:
        for otro in interacciones[m["user"]]:
            conteo[(m["user"], otro)] += interacciones[m["user"]][otro]
    texto = "\n".join([f"{a} → {b}: {n}" for (a, b), n in conteo.most_common(10)])
    await update.message.reply_text(f"📈 Ranking de menciones:\n{texto}")

async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pareja = calcular_pareja(1)
    if pareja:
        await update.message.reply_text(f"💘 Pareja del día: {pareja[0]} & {pareja[1]}")
    else:
        await update.message.reply_text("No hay suficientes datos aún.")

async def pareja_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pareja = calcular_pareja(7)
    if pareja:
        await update.message.reply_text(f"💞 Pareja de la semana: {pareja[0]} & {pareja[1]}")
    else:
        await update.message.reply_text("No hay suficientes datos aún.")

async def pareja_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pareja = calcular_pareja(30)
    if pareja:
        await update.message.reply_text(f"💍 Pareja del mes: {pareja[0]} & {pareja[1]}")
    else:
        await update.message.reply_text("No hay suficientes datos aún.")

if __name__ == "__main__":
    cargar()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("interacciones", interacciones_cmd))
    app.add_handler(CommandHandler("menciones_juan", menciones_juan))
    app.add_handler(CommandHandler("ranking_menciones", ranking_menciones))
    app.add_handler(CommandHandler("pareja_dia", pareja_dia))
    app.add_handler(CommandHandler("pareja_semana", pareja_semana))
    app.add_handler(CommandHandler("pareja_mes", pareja_mes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()
