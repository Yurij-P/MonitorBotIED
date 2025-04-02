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
            print("Таблиця завантажена:", len(data), "рядків")
            return data
        else:
            print("Відсутні потрібні колонки:", data.columns.tolist())
            return pd.DataFrame()
    except Exception as e:
        print("Помилка при зчитуванні:", e)
        return pd.DataFrame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Надішліть назву об'єкта для перевірки.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш ID: {update.effective_user.id}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    status = "Завантажено" if not df.empty else "Не завантажено"
    await update.message.reply_text(f"Стан таблиці: {status}, записів: {len(df)}")

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("База не завантажена. Надішліть Excel.")
        return

    query = update.message.text.lower()
    matches = df[df["Об'єкт"].astype(str).str.lower().str.contains(query, na=False)]

    if not matches.empty:
        results = []
        for _, row in matches.head(3).iterrows():
            results.append("Обʼєкт: {}\nОбласть: {}\nКонкурс: {}\nМоніторинг: {}".format(
    row["Обʼєкт"],
    row["Область"],
    row["Конкурс (1 - відновлення, 2 закупівлі)"],
    row["Хто здійснює моніторинг"]
))
        await update.message.reply_text("Знайдено:

" + "

".join(results))
    else:
        await update.message.reply_text("Об'єкт не знайдено у базі.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У вас немає прав для оновлення таблиці.")
        return

    file = update.message.document
    if not file.file_name.endswith(".xlsx"):
        await update.message.reply_text("Надішліть Excel-файл (.xlsx)")
        return

    await update.message.reply_text("Завантажую...")
    try:
        new_file = await file.get_file()
        await new_file.download_to_drive("monitoring.xlsx")
        df = load_data()
        if df.empty:
            await update.message.reply_text("Помилка зчитування.")
        else:
            await update.message.reply_text("Таблиця оновлена.")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {e}")

async def run_bot():
    print("Бот запускається...")
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
            print("Бот працює.")
            await app.updater.start_polling()
            await app.updater.idle()
        except NetworkError as e:
            print("Мережева помилка:", e)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
