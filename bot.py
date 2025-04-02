import pandas as pd
import warnings
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError
import asyncio

warnings.filterwarnings("ignore", category=UserWarning)

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
df = pd.DataFrame()

def load_data():
    try:
        data = pd.read_excel("monitoring.xlsx")
        required_cols = ["Об'єкт", "Область", "Конкурс (1 - відновлення, 2 закупівлі)", "Хто здійснює моніторинг"]
        if all(col in data.columns for col in required_cols):
            print("✅ Таблиця успішно завантажена")
            return data[data["Об'єкт"].notna()]
        else:
            print("❌ Відсутні потрібні колонки в таблиці")
            return pd.DataFrame()
    except Exception as e:
        print("❌ Помилка при зчитуванні таблиці:", e)
        return pd.DataFrame()

df = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву обʼєкта — я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш Telegram ID: {update.effective_user.id}")

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("⚠️ База ще не завантажена. Надішліть Excel-файл.")
        return

    query = update.message.text.lower()
    matches = df[df["Об'єкт"].str.lower().str.contains(query, na=False)]

    if not matches.empty:
        results = []
        for _, row in matches.iterrows():
            obj = row["Об'єкт"]
            oblast = row["Область"]
            contest = row["Конкурс (1 - відновлення, 2 закупівлі)"]
            monitor = row["Хто здійснює моніторинг"]
            results.append(f"🏗 {obj}\n📍 {oblast}\n📊 Конкурс: {contest}\n👀 Моніторинг: {monitor}")
        await update.message.reply_text("✅ Знайдено:\n\n" + "\n\n".join(results[:3]))
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
    try:
        new_file = await file.get_file()
        await new_file.download_to_drive("monitoring.xlsx")
        df = load_data()
        if df.empty:
            await update.message.reply_text("❌ Помилка: таблиця порожня або має неправильний формат.")
        else:
            await update.message.reply_text("✅ Таблиця успішно оновлена!")
    except Exception as e:
        await update.message.reply_text(f"❌ Не вдалося завантажити таблицю: {e}")

async def run_bot():
    print("🚀 run_bot() почався")
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_object))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_file))

    # Повідомлення адміну про запуск
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(chat_id=admin_id, text="✅ Бот запущено. Очікує об'єкти для перевірки.")
        except Exception as e:
            print(f"⚠️ Не вдалося надіслати адміну {admin_id}: {e}")

    while True:
        try:
            await app.initialize()
            await app.start()
            print("✅ Бот працює. Очікує повідомлень...")
            await app.updater.start_polling()
            await app.updater.idle()
        except NetworkError as e:
            print("🔁 Мережева помилка. Повтор через 10 сек...", e)
            await asyncio.sleep(10)

if __name__ == "__main__":
    print("✅ Бот стартує...")
    asyncio.run(run_bot())
