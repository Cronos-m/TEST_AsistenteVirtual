import os
import json
import requests

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

# Cargar variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Cargar conocimiento
with open("knowledge.json", "r", encoding="utf-8") as file:
    knowledge = json.load(file)

SYSTEM_PROMPT = f"""
Eres un asistente virtual profesional y humano.

Información REAL de la empresa:

{json.dumps(knowledge, indent=2, ensure_ascii=False)}

Reglas IMPORTANTES:
- Nunca inventes información.
- Usa únicamente la información proporcionada.
- Si no sabes algo, dilo honestamente.
- Responde de manera amable, humana y natural.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.7
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    result = response.json()

    reply = result["choices"][0]["message"]["content"]

    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

print("Bot funcionando con Groq...")

app.run_polling()