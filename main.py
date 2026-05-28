import os
import json
import asyncio
import requests

from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# VARIABLES
# =========================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================
# KNOWLEDGE
# =========================

with open("knowledge.json", "r", encoding="utf-8") as file:
    knowledge = json.load(file)

SYSTEM_PROMPT = f"""
Eres un asistente virtual profesional, humano y amable.

Información REAL de la empresa:

{json.dumps(knowledge, indent=2, ensure_ascii=False)}

REGLAS IMPORTANTES:
- Nunca inventes información.
- Usa únicamente la información proporcionada.
- Si no sabes algo, dilo honestamente.
- Responde de forma natural y útil.
"""

# =========================
# TELEGRAM APP
# =========================

application = Application.builder().token(TELEGRAM_TOKEN).build()

# =========================
# IA RESPONSE
# =========================

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

# =========================
# HANDLER
# =========================

application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():

    data = request.get_json(force=True)

    update = Update.de_json(data, application.bot)

    asyncio.run(application.process_update(update))

    return "ok"

# =========================
# STARTUP
# =========================

asyncio.run(application.initialize())

print("Bot webhook funcionando")
