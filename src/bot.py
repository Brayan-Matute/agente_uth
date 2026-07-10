# -*- coding: utf-8 -*-
"""
bot.py
Integracion del Agente Virtual con la API de Telegram (python-telegram-bot).
Utiliza el mismo motor (chatbot_engine.py) que la interfaz web, garantizando
una unica fuente de verdad para la base de conocimiento y la logica de
clasificacion de intencion.

Segundo Avance - Agente Virtual Guia para Orientacion Universitaria (UTH)

Requisitos:
    pip install python-telegram-bot==21.*

Configuracion:
    Establecer la variable de entorno TELEGRAM_BOT_TOKEN con el token
    obtenido desde @BotFather en Telegram.

Ejecucion:
    python bot.py
"""

import os
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from chatbot_engine import ChatbotEngine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

engine = ChatbotEngine()

MENU_PRINCIPAL = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏢 Infraestructura", callback_data="cat_Infraestructura")],
    [InlineKeyboardButton("🕒 Horarios", callback_data="cat_Horarios")],
    [InlineKeyboardButton("📄 Tramites Academicos", callback_data="cat_Procesos Academicos")],
    [InlineKeyboardButton("💬 Soporte y Cuentas", callback_data="cat_Soporte y Cuentas")],
    [InlineKeyboardButton("🙋 Hablar con un asesor", callback_data="transferir")],
])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu Asistente Universitario Virtual 🎓\n"
        "¿En que puedo ayudarte hoy?",
        reply_markup=MENU_PRINCIPAL
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Estas son las categorias disponibles:",
                                     reply_markup=MENU_PRINCIPAL)


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = f"tg-{update.effective_chat.id}"
    texto_usuario = update.message.text

    resultado = engine.procesar_mensaje(texto_usuario, session_id)
    await update.message.reply_text(resultado["texto"], reply_markup=MENU_PRINCIPAL)


async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    session_id = f"tg-{query.message.chat_id}"

    if data == "transferir":
        resultado = engine.procesar_mensaje("hablar con un asesor", session_id)
        await query.edit_message_text(resultado["texto"])
        return

    categoria = data.replace("cat_", "")
    faqs = engine.listar_faqs_por_categoria(categoria)
    if not faqs:
        await query.edit_message_text("No encontre preguntas para esa categoria.")
        return

    botones = [
        [InlineKeyboardButton(f["pregunta"][:60], callback_data=f"faq_{f['id']}")]
        for f in faqs[:8]
    ]
    botones.append([InlineKeyboardButton("⬅️ Volver al menu", callback_data="volver_menu")])
    await query.edit_message_text(
        f"Preguntas frecuentes - {categoria}:",
        reply_markup=InlineKeyboardMarkup(botones)
    )


async def manejar_faq_directa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "volver_menu":
        await query.edit_message_text("Menu principal:", reply_markup=MENU_PRINCIPAL)
        return

    faq_id = data.replace("faq_", "")
    faq_encontrada = None
    for faq in engine.faqs:
        if faq["id"] == faq_id:
            faq_encontrada = faq
            break

    if faq_encontrada:
        await query.edit_message_text(faq_encontrada["respuesta"])
    else:
        await query.edit_message_text("No pude encontrar esa respuesta.")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Debes establecer la variable de entorno TELEGRAM_BOT_TOKEN "
            "con el token de tu bot (obtenido desde @BotFather)."
        )

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CallbackQueryHandler(manejar_boton, pattern="^cat_|^transferir$"))
    app.add_handler(CallbackQueryHandler(manejar_faq_directa, pattern="^faq_|^volver_menu$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot de Telegram iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
