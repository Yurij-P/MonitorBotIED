import pandas as pd
import warnings
import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from telegram.error import NetworkError

warnings.filterwarnings("ignore", category=UserWarning)

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
df = pd.DataFrame()

def load_data():
    try:
        data = pd.read_excel("monitoring.xlsx")
        data.columns = data.columns.str.strip()

        print("🧾 Колонки в Excel:", list(data.columns))

        expected_keywords = ['об’єкт', 'область', 'конкурс', 'моніторинг']
        matched = [col for col in data.columns if any(kw in col.lower() for kw in expected_keywords)]

        if len(matched) >= 4:
            print("✅ Таблиця має очікувані колонки:", matched)
            return data[data[matched[0]].notna()]
        else:
            print("❌ Не всі очікувані колонки знайдено.")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Помилка при завантаженні Excel: {e}")
        return pd.DataFrame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву об’єкта – я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш Telegram ID: {update.effective_user.id}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    status = "✅ Завантажено" if not df.empty else "❌ Не завантажено"
    await update.message.reply_text(f"🗂️ Стан таблиці: {status} | Записів: {len(df)}")

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("⚠️ База не завантажена.")
        return

    query = update.message.text.lower()
    matches = df[df[df.columns[0]].astype(str).str.lower().str.contains(query, na=False)]

    if not matches.empty:
        results = []
        for _, row in matches.head(3).iterrows():
            result = (
                f"🏢 Об’єкт: {row[df.columns[0]]}\\n"
                f"📍 Область: {row[df.columns[1]]}\\n"
                f"📋 Конкурс: {row[df.columns[2]]}\\n"
                f"👁️ Моніторинг: {row[df.columns[3]]}"
            )
            results.append(result)
        await update.message.reply_text("🔍 Знайдено:" + "\n\n".join(results))
    else:
        await update.message.reply_text("❌ Об’єкт не знайдено в таблиці.")

if __name__ == "__main__":
    df = load_data()

    async def run_bot():
        while True:
            try:
                app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
                app.add_handler(CommandHandler("start", start))
                app.add_handler(CommandHandler("id", get_id))
                app.add_handler(CommandHandler("debug", debug))
                app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_object))
                await app.initialize()
                await app.start()
                await app.updater.start_polling()
                await app.updater.idle()
            except NetworkError as e:
                print("🌐 Мережева помилка. Повтор через 10 секунд...", e)
                await asyncio.sleep(10)

    asyncio.run(run_bot())
