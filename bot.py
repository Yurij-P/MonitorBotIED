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
table_loaded = False

def load_data():
    try:
        data = pd.read_excel("monitoring.xlsx")
        required_cols = ["Об'єкт", "Область", "Конкурс (1 - відновлення, 2 закупівлі)", "Хто здійснює моніторинг"]
        if all(col in data.columns for col in required_cols):
            print("✅ Таблиця успішно завантажена:", len(data), "рядків")
            return data
        else:
            print("❌ Відсутні колонки в таблиці:", data.columns.tolist())
            return pd.DataFrame()
    except Exception as e:
        print("❌ Помилка при зчитуванні Excel:", e)
        return pd.DataFrame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву об’єкта — я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш Telegram ID: {update.effective_user.id}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    status = "✅ Завантажено" if not df.empty else "❌ НЕ завантажено"
    await update.message.reply_text(f"📊 Стан таблиці: {status}, записів: {len(df)}")

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("⚠️ База ще не завантажена. Надішліть Excel-файл.")
        return

    query = update.message.text.lower()
    matches = df[df["Об'єкт"].astype(str).str.lower().str.contains(query, na=False)]

    if not matches.empty:
        results = []
        for _, row in matches.head(3).iterrows():
            results.append(
                f"🏗 {row["Об'єкт"]}
📍 {row["Область"]}
📊 Конкурс: {row["Конкурс (1 - відновлення, 2 закупівлі)"]}
👀 Моніторинг: {row["Хто здійснює моніторинг"]}"
            )
        await update.message.reply_text("✅ Знайдено:

" + "

".join(results))
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
        await update.message.reply_text("❌ Надішліть файл Excel (.xlsx)")
        return

    await update.message.reply_text("⏳ Завантажую таблицю...")
    try:
        new_file = await file.get_file()
        await new_file.download_to_drive("monitoring.xlsx")
        df = load_data()
        if df.empty:
            await update.message.reply_text("❌ Таблиця не зчиталась або має помилковий формат.")
        else:
            await update.message.reply_text("✅ Таблиця успішно оновлена.")
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка при зчитуванні: {e}")

async def run_bot():
    print("✅ Бот стартує...")
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("debug", debug))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_object))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file))

    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(chat_id=admin_id, text="✅ Бот запущено. Готовий до роботи.")
        except:
            pass

    while True:
        try:
            await app.initialize()
            await app.start()
            print("✅ Бот працює")
            await app.updater.start_polling()
            await app.updater.idle()
        except NetworkError as e:
            print("🔁 Мережева помилка:", e)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
