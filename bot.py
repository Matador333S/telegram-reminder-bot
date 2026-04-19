print("BOT STARTED")

import json
import os
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8632973637:AAEc7WZULKqcOMdtvbPy323y9PFlC23LOl8"

DATA_FILE = "data.json"

# ------------------ STORAGE ------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

data = load_data()

# ------------------ UI ------------------

def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ +10 хв", callback_data="snooze")],
        [InlineKeyboardButton("💛 я умнічка", callback_data="done")]
    ])

# ------------------ START ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💛 Привіт, маленька)\n"
        "Напиши час нагадування у форматі HH:MM\n"
        "Наприклад: 21:30"
    )

# ------------------ SET TIME ------------------

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text

    try:
        target_time = datetime.strptime(text, "%H:%M").time()
        now = datetime.now()

        target = datetime.combine(now.date(), target_time)

        if target < now:
            target += timedelta(days=1)

        delay = (target - now).total_seconds()

        # зберігаємо
        data[chat_id] = text
        save_data(data)

        async def reminder():
            await asyncio.sleep(delay)
            await context.bot.send_message(
                chat_id=chat_id,
                text="💛 Час зробити те, що ти планувала",
                reply_markup=keyboard()
            )

        asyncio.create_task(reminder())

        await update.message.reply_text(f"💛 Збережено! Нагадую о {text}")

    except:
        await update.message.reply_text("❌ Формат: HH:MM")

# ------------------ BUTTONS ------------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    if query.data == "snooze":

        async def later():
            await asyncio.sleep(600)
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏰ нагадую ще раз",
                reply_markup=keyboard()
            )

        asyncio.create_task(later())
        await query.edit_message_text("⏰ Добре, через 10 хв ще раз")

    elif query.data == "done":
        await query.edit_message_text("💛 Я умнічка ✨")

# ------------------ RESTORE ------------------

async def restore_tasks(app):
    for chat_id, time_str in data.items():
        try:
            target_time = datetime.strptime(time_str, "%H:%M").time()
            now = datetime.now()

            target = datetime.combine(now.date(), target_time)

            if target < now:
                target += timedelta(days=1)

            delay = (target - now).total_seconds()

            async def reminder(cid=chat_id):
                await asyncio.sleep(delay)
                await app.bot.send_message(
                    chat_id=cid,
                    text="💛 Нагадування після перезапуску",
                    reply_markup=keyboard()
                )

            asyncio.create_task(reminder())

        except:
            pass

# ------------------ LIFECYCLE FIX ------------------

async def post_init(app):
    await restore_tasks(app)

# ------------------ APP ------------------

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .post_init(post_init)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_time))
app.add_handler(CallbackQueryHandler(buttons))

print("BOT RUNNING")

app.run_polling(drop_pending_updates=True)