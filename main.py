import asyncio
import re
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ===== TELETHON CONFIG (USER ACCOUNT) =====
API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
TARGET_BOT = "@botbysahilbot"

tele_client = TelegramClient("session_final", API_ID, API_HASH)

# ===== BOT CONFIG =====
BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"

# ===== TELETHON LISTENER =====
@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def handle_target_response(event):
    text = event.text or ""

    match = re.search(r"CMD:\s*(.+)", text)
    if match:
        final_cmd = match.group(1)
        print("✅ FINAL RESPONSE:", final_cmd)

        # save optional
        with open("output.txt", "w") as f:
            f.write(final_cmd)

# ===== BOT COMMAND =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Processing…")

    # ensure telethon connected
    if not tele_client.is_connected():
        await tele_client.start()

    # interact with target bot
    await tele_client.send_message(TARGET_BOT, "/start")
    await asyncio.sleep(2)
    await tele_client.send_message(
        TARGET_BOT,
        "/status https://t.me/examplegroup"
    )

    await update.message.reply_text("📤 Command sent, waiting for response…")

# ===== MAIN =====
async def main():
    await tele_client.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 Bot + Telethon running")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())