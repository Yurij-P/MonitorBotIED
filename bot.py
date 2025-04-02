import pandas as pd
import warnings
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError
import asyncio

warnings.filterwarnings("ignore", category=UserWarning)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

def load_data():
    try:
        data = pd.read_excel("monitoring.xlsx", skiprows=2)
        return data[data["Об'єкт"].notna()]
    except Exception as e:
        print("❌ Excel помилка:", e)
        return pd.DataFrame()

df = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву обʼєкта — я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш Telegram ID: {update.effective_user.id}")

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    query = update.message.text.lower()
    matches = df[df["Об'єкт"].str.lower().str.contains(query, na=False)]
    if not matches.empty:
        results = []
        for _, row in matches.head(3).iterrows():
            obj = row["Об'єкт"]
            monitor = row["Хто здійснює моніторинг"]
            text = f"🏗 {obj}\n👀 Моніторинг: {monitor}"
            results.append(text)
        await update.message.reply_text("✅ Знайдено:\n\n" + "\n\n".join(results))
    else:
        await update.message.reply_text("❌ Об'єкт не знайдено у базі моніторингу.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 У вас немає прав для оновлення таблиці.")
        return
    file = update.message.document
    if not file.file_name.endswith(".xlsx"):
        await update.message.reply_text("❌ Надішліть файл у форматі Excel (.xlsx)")
        return
    await update.message.reply_text("⏳ Завантажую нову таблицю...")
    new_file = await file.get_file()
    await new_file.download_to_drive("monitoring.xlsx")
    df = load_data()
    await update.message.reply_text("✅ Таблиця оновлена!")

async def run_bot():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_object))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file))
    while True:
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            await app.updater.idle()
        except NetworkError as e:
            print("🔁 Мережева помилка. Повтор через 10 сек...", e)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
