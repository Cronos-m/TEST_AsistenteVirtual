import os
import json
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, Request
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

INFORMACIÓN EMPRESA:

{json.dumps(knowledge, indent=2, ensure_ascii=False)}

Si saludan, responde:
"Hola 😊 Hablas con Sandra de {knowledge["empresa"]}. ¿En qué puedo ayudarte?"
"""

# =========================
# TELEGRAM APP
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
# FASTAPI
# =========================

app = FastAPI()

@app.on_event("startup")
async def startup():

    await application.initialize()

@app.get("/")
async def root():

    return {"status": "ok"}

@app.post(f"/{TELEGRAM_TOKEN}")
async def webhook(request: Request):

    data = await request.json()

    update = Update.de_json(data, application.bot)

    await application.process_update(update)

    return {"ok": True}
