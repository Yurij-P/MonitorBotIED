
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
        required_cols = ['Обʼєкт', 'Область', "Конкурс (1 – відновлення, 2 закупівлі)", "Хто здійснює моніторинг"]
        if all(col in data.columns for col in required_cols):
            print("✅ Таблиця успішно завантажена")
            return data[data['Обʼєкт'].notna()]
        else:
            print("❌ Відсутні потрібні колонки в таблиці")
            return pd.DataFrame()
    except Exception as e:
        print("❌ Помилка при зчитуванні таблиці:", e)
        return pd.DataFrame()

df = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли назву обʼєкта – я перевірю, чи він вже під моніторингом.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш Telegram ID: {update.effective_user.id}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    status = "✅ Завантажено" if not df.empty else "❌ Не завантажено"
    await update.message.reply_text("📊 Стан таблиці: {} | Записів: {}".format(status, len(df)))

async def check_object(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    if df.empty:
        await update.message.reply_text("⚠️ База не завантажена. Надішліть Excel-файл.")
        return

    query = update.message.text.lower()
    matches = df[df["Обʼєкт"].astype(str).str.lower().str.contains(query, na=False)]

    if not matches.empty:
        results = []
        for _, row in matches.head(3).iterrows():
            result = (
                f"🏗 Обʼєкт: {row['Обʼєкт']}"
                f"📍 Область: {row['Область']}"
                f"🏛 Конкурс: {row['Конкурс (1 – відновлення, 2 закупівлі)']}"
                f"👀 Моніторинг: {row['Хто здійснює моніторинг']}"
            )
            results.append(result)
        await update.message.reply_text(f"🔍 Знайдено:

" + "

".join(results))
    else:
        await update.message.reply_text("❌ Обʼєкт не знайдено в таблиці.")

if __name__ == "__main__":
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
                print("🔁 Мережева помилка. Повтор через 10 секунд...", e)
                await asyncio.sleep(10)

    asyncio.run(run_bot())
