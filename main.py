import os
import json
import asyncio
import threading
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

# =========================
# PROMPT
# =========================

SYSTEM_PROMPT = f"""
Eres Sandra, asesora virtual de {knowledge["empresa"]}.

Tu personalidad:
- amable
- humana
- cercana
- profesional
- breve

REGLAS:
- Responde corto.
- No hagas respuestas largas.
- No inventes información.
- Usa únicamente la información proporcionada.
- Habla como una persona real por chat.

INFORMACIÓN DE LA EMPRESA:

{json.dumps(knowledge, indent=2, ensure_ascii=False)}

SALUDO:
Si el usuario saluda, responde algo parecido a:
"Hola 😊 Hablas con Sandra de {knowledge["empresa"]}. ¿En qué puedo ayudarte?"
"""

# =========================
# TELEGRAM
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
        "temperature": 0.5,
        "max_tokens": 150
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

        reply = "Lo siento, ocurrió un problema."

    await update.message.reply_text(reply)

# =========================
# HANDLER
# =========================

application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# =========================
# EVENT LOOP GLOBAL
# =========================

loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

asyncio.run_coroutine_threadsafe(
    application.initialize(),
    loop
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

        update = Update.de_json(data, application.bot)

        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            loop
        )

        future.result()

        return "ok"

    except Exception as error:

        print("ERROR:")
        print(error)

        return "error", 500
