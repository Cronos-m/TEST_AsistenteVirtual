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
# CARGAR INFORMACIÓN
# =========================

with open("knowledge.json", "r", encoding="utf-8") as file:
    knowledge = json.load(file)

# =========================
# PROMPT DEL SISTEMA
# =========================

SYSTEM_PROMPT = f"""
Eres un asesor humano, amable y profesional de una empresa llamada TU EMPRESA.

Tu objetivo es ayudar clientes de manera natural y cercana.

Información REAL de la empresa:

{json.dumps(knowledge, indent=2, ensure_ascii=False)}

REGLAS IMPORTANTES:
- Nunca inventes información.
- Usa únicamente la información proporcionada.
- Sé natural y conversacional.
- Sé breve y útil.
- Si no sabes algo, dilo honestamente.
- Si te quedas sin información o el cliente pide hablar con alguien diferente a ti comunicalo al 3002660164
"""

# =========================
# TELEGRAM
# =========================

application = Application.builder().token(TELEGRAM_TOKEN).build()

# =========================
# RESPUESTA IA
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
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

    except Exception as error:

        print(error)

        reply = "Lo siento, ocurrió un problema procesando tu solicitud."

    await update.message.reply_text(reply)

# =========================
# HANDLER MENSAJES
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
    return "Bot funcionando correctamente"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():

    try:

        data = request.get_json(force=True)

        print("MENSAJE RECIBIDO:")
        print(data)

        update = Update.de_json(data, application.bot)

        asyncio.run(application.process_update(update))

        return "ok"

    except Exception as error:

        print("ERROR WEBHOOK:")
        print(error)

        return "error", 500

# =========================
# INICIALIZAR BOT
# =========================

asyncio.run(application.initialize())

print("Bot webhook funcionando correctamente")
