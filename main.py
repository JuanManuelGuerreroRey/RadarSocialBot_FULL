RadarSocialBot - Versión de prueba

from telegram import Update from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes import json from collections import defaultdict

Variables simuladas para esta prueba

TOKEN = "AQUÍ_TU_TOKEN" GROUP_ID = -1001169225264

Diccionarios globales

interacciones = defaultdict(lambda: defaultdict(int)) mensajes_por_usuario = defaultdict(int) menciones_a_juan = defaultdict(int) mensaje_count = 0

Comando para mostrar top de mensajes por usuario

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE): top = sorted(mensajes_por_usuario.items(), key=lambda x: x[1], reverse=True) texto = "\ud83d\udcca Top usuarios activos:\n" + "\n".join([f"{k}: {v} mensajes" for k, v in top]) await context.bot.send_message(chat_id=update.effective_chat.id, text=texto)

Comando para mostrar interacciones

async def interacciones_globales(update: Update, context: ContextTypes.DEFAULT_TYPE): texto = "\ud83d\udcc8 Interacciones globales:\n" for u1 in interacciones: for u2 in interacciones[u1]: texto += f"{u1} → {u2}: {interacciones[u1][u2]} interacciones\n" await context.bot.send_message(chat_id=update.effective_chat.id, text=texto)

Comando para mostrar menciones a Juan

async def menciones_juan(update: Update, context: ContextTypes.DEFAULT_TYPE): texto = "\ud83d\udcc4 Menciones a Juan:\n" for usuario, count in menciones_a_juan.items(): texto += f"{usuario}: {count} menciones\n" if not menciones_a_juan: texto += "Nadie ha mencionado a Juan aún." await context.bot.send_message(chat_id=update.effective_chat.id, text=texto)

Comando de contador para debug

async def contador(update: Update, context: ContextTypes.DEFAULT_TYPE): await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Mensajes contados: {mensaje_count}")

Comando resumen cada 30 mensajes (modo prueba)

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE): if mensaje_count >= 30: await context.bot.send_message(chat_id=update.effective_chat.id, text="\ud83d\udd39 Resumen del grupo: En el grupo ha habido bastante actividad con varias menciones e interacciones interesantes.") else: await context.bot.send_message(chat_id=update.effective_chat.id, text="Aún no hay suficientes mensajes para generar un resumen.")

Comando pareja del día (activado cuando hay suficiente interacción)

async def pareja_dia(update: Update, context: ContextTypes.DEFAULT_TYPE): top = ("", "", 0) for u1 in interacciones: for u2 in interacciones[u1]: if interacciones[u1][u2] > top[2]: top = (u1, u2, interacciones[u1][u2]) if top[2] >= 10: await context.bot.send_message(chat_id=update.effective_chat.id, text=f"💑 Pareja del día: {top[0]} & {top[1]} con {top[2]} interacciones") else: await context.bot.send_message(chat_id=update.effective_chat.id, text="Aún no hay suficiente interacción para determinar pareja del día.")

Registrar mensajes

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE): global mensaje_count user = update.effective_user.first_name reply_to = update.message.reply_to_message

mensajes_por_usuario[user] += 1
mensaje_count += 1

if "juan" in update.message.text.lower():
    menciones_a_juan[user] += 1

if reply_to:
    otro = reply_to.from_user.first_name
    interacciones[user][otro] += 1

MAIN

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("stats", stats)) app.add_handler(CommandHandler("interacciones", interacciones_globales)) app.add_handler(CommandHandler("menciones_juan", menciones_juan)) app.add_handler(CommandHandler("contador", contador)) app.add_handler(CommandHandler("resumen", resumen)) app.add_handler(CommandHandler("pareja_dia", pareja_dia)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))

app.run_polling()

