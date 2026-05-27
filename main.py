from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv
import os
import requests

# Cargar variables del .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Función que habla con Ollama
def ask_ai(message):

    prompt = f"""
    Responde como un asistente de atención al cliente.
    Habla de forma natural y humana.
    No hables como robot.
    Sé amable y breve.

    Cliente:
    {message}
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    return data["response"]

# Manejar mensajes de Telegram
async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_message = update.message.text

    ai_response = ask_ai(user_message)

    await update.message.reply_text(ai_response)

# Crear aplicación Telegram
app = ApplicationBuilder().token(TOKEN).build()

# Escuchar mensajes
app.add_handler(
    MessageHandler(
        filters.TEXT,
        handle_message
    )
)

print("Bot funcionando...")

# Iniciar bot
app.run_polling()