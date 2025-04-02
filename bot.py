import pandas as pd
import os
import warnings
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import NetworkError

warnings.filterwarnings("ignore", category=UserWarning)

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
df = pd.DataFrame()

def load_data():
    try:
        data = pd.read_excel("monitoring.xlsx")
        required_cols = ["Об'єкт", "Область", "Конкурс (1 - відновлення, 2 закупівлі)", "Хто здійснює моніторинг"]
        if all(col in data.columns for col in required_cols):
            print("✅ Таблиця завантажена:", len(data), "рядків")
            return data
        else:
            print("❌ Відсутні деякі колонки:", data.columns.tolist())
            return pd.DataFrame()
    except Exception as e:
        print("❌ Помилка при зчитуванні:", e)
        return pd.DataFrame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву обʼєкта — я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆔 Ваш Telegram ID: {}".format(update.effective_user.id))

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    status = "✅ Завантажено" if not df.empty else "❌ Не завантажено"
    await update.message.reply_text("🧾 Стан таблиці: {} | Записів: {}".format(status, len(df)))

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("⚠️ База не завантажена. Надішліть Excel-файл.")
        return

    query = update.message.text.lower()
    matches = df[df["Об'єкт"].astype(str).str.lower().str.contains(query, na=False)]
    if not matches.empty:
    results = []
    for _, row in matches.head(3).iterrows():
        result = (
    f"🏗 Обʼєкт: {row['Обʼєкт']}\n"
    f"📍 Область: {row['Область']}\n"
    f"🏛 Конкурс: {row['Конкурс (1 – відновлення, 2 закупівлі)']}\n"
    f"👀 Моніторинг: {row['Хто здійснює моніторинг']}"
)

    await update.message.reply_text(f"🔎 Знайдено:\n\n" + "\n\n".join(results))
else:
    await update.message.reply_text("❌ Обʼєкт не знайдено в таблиці.")
            )
            results.append(result)
        await update.message.reply_text("🔍 Знайдено:

" + "

".join(results))
    else:
        await update.message.reply_text("❌ Обʼєкт не знайдено у базі моніторингу.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 У вас немає прав для оновлення.")
        return

    file = update.message.document
    if not file.file_name.endswith(".xlsx"):
        await update.message.reply_text("❌ Надішліть файл у форматі .xlsx")
        return

    await update.message.reply_text("⏳ Завантаження таблиці...")
    try:
        new_file = await file.get_file()
        await new_file.download_to_drive("monitoring.xlsx")
        df = load_data()
        if df.empty:
            await update.message.reply_text("❌ Таблиця не оновлена. Перевірте формат.")
        else:
            await update.message.reply_text("✅ Таблиця успішно оновлена.")
    except Exception as e:
        await update.message.reply_text("❌ Сталася помилка: {}".format(str(e)))

async def run_bot():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("debug", debug))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_object))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file))

    while True:
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            await app.updater.idle()
        except NetworkError as e:
            print("🔁 Мережева помилка:", e)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
