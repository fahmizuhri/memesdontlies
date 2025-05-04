import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
import re

# Load token dari .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

def start(update, context):
    update.message.reply_text("Selamat datang di bot evaluasi sinyal token! Kirimkan sinyal token untuk evaluasi.")

def parse_signal(text: str) -> dict:
    header_re = re.compile(r"💊\s*#(?P<chain>\w+) - (?P<name>.*?) ｜ \$(?P<symbol>\S+)")
    cap_re = re.compile(r"💸 Market Cap: \$(?P<cap>[\d\.]+)(?P<unit>k|M)?")
    bundle_re = re.compile(r"📦 Bundle: *[\d\.]+ \w+ ⋅ (?P<bundle_pct>[\d\.]+)% ⇨ (?P<sell_pct>[\d\.]+)%")
    holders_re = re.compile(r"👫 Holder: (?P<holders>\d+)")
    top10_re = re.compile(r"💪 TOP 10: (?P<top10>\d+)%")
    vol1h_re = re.compile(r"💰 Last 1h: \$(?P<vol1h>[\d\.]+)k")
    age_re = re.compile(r"⌛️ Pool Age: (?P<age>\d+) minutes? ago")

    data = {}
    if m := header_re.search(text): data.update(m.groupdict())
    if m := cap_re.search(text):
        val = float(m.group('cap')) * (1e3 if m.group('unit') == 'k' else 1e6 if m.group('unit') == 'M' else 1)
        data['market_cap'] = val
    if m := bundle_re.search(text): data['bundle_pct'] = float(m.group('bundle_pct'))
    if m := holders_re.search(text): data['holders'] = int(m.group('holders'))
    if m := top10_re.search(text): data['top10_pct'] = int(m.group('top10'))
    if m := vol1h_re.search(text): data['vol_1h'] = float(m.group('vol1h')) * 1000
    if m := age_re.search(text): data['pool_age_min'] = int(m.group('age'))
    return data

def score_signal(data: dict) -> tuple:
    score = 0
    reasons = []

    if data.get("market_cap", 0) < 20000:
        score += 1; reasons.append("💸 Low Market Cap")
    if data.get("bundle_pct", 0) > 10:
        score += 1; reasons.append("📦 High Bundle %")
    if data.get("holders", 0) > 100:
        score += 1; reasons.append("👫 Decent Holders")
    if data.get("top10_pct", 100) < 20:
        score += 1; reasons.append("💪 Low Top10%")
    if data.get("vol_1h", 0) > 10000:
        score += 1; reasons.append("🎮 Volume 1H Active")
    if data.get("pool_age_min", 999) < 10:
        score += 1; reasons.append("⌛️ Fresh Pool")

    label = "✅ GOOD SIGNAL" if score >= 5 else "⚠️ AVERAGE" if score >= 3 else "❌ BAD SIGNAL"
    return label, score, reasons

def handle_signal(update, context):
    text = update.message.text
    data = parse_signal(text)
    if not data:
        update.message.reply_text("❌ Format tidak dikenali.")
        return
    label, score, reasons = score_signal(data)
    message = f"{label}\nScore: {score}/6\n" + "\n".join(reasons)

    keyboard = InlineKeyboardMarkup([[ 
        InlineKeyboardButton("🔼 Token Naik", callback_data='up'),
        InlineKeyboardButton("🔽 Rugpull", callback_data='down'),
        InlineKeyboardButton("⚠️ Flat", callback_data='flat'),
    ]])

    update.message.reply_text(message, reply_markup=keyboard)

def handle_feedback(update, context):
    query = update.callback_query
    feedback = query.data
    query.edit_message_reply_markup(reply_markup=None)
    query.message.reply_text(f"✅ Feedback disimpan: {feedback}")

    # Ambil pesan sinyal asli
    signal_text = query.message.text

    # Ekstrak label (Good/Average/Bad) dari baris pertama pesan
    lines = signal_text.splitlines()
    label = lines[0].strip() if lines else ""

    # Simpan ke file CSV
    with open("feedback_log.csv", "a", encoding="utf-8") as f:
        f.write(f'"{label}","{feedback}"\n')

def main():
    # Update: gunakan Updater tanpa `use_context=True` pada versi 13.15
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_signal))
    dp.add_handler(CallbackQueryHandler(handle_feedback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
