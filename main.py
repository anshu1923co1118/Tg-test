import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== TELETHON CONFIG =====
API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"

STRING_SESSION = (
    "1BVtsOKEBu73mh4SW00pWPqOS8h6p4Gk6bVtQ5bgBPMaR645jIhARGSfzkmyEQEYhOAh2AEv8mq9EZL86Zd95StVzPwWaQLNl-EbOp5fVVeFK_ZUuN93mEZFMEuF7o6LCMgbJwvgVQuWQdycOnB652OY_zzZvOLcOPxWuLQOvLIuwtoYpNvL3Qs_PfGGHNAojo7k-NgMFURnj_UP0rh7RRDvAWN7lT1_jzma5dn7HhkPgsrwSieDtgqBkDftRxZQc9FYG2iYmyoJarEhfrqn3UbrueWqN0XiO983MRg-EavUGFWPNQ4QnQgUEf-uptcaeroorCOBv0gCfr3DjpFv4oLrG-SHkrFA="
)

TARGET_BOT = "@botbysahilbot"

tele_client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

# ===== TELEGRAM BOT CONFIG =====
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ===== TELETHON LISTENER =====
@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def handle_target_response(event):
    print("📩 RAW:", event.text)

    match = re.search(r"CMD:\s*(.+)", event.text or "")
    if match:
        cmd = match.group(1)
        print("✅ FINAL CMD:", cmd)

        with open("output.txt", "w") as f:
            f.write(cmd)

# ===== BOT COMMAND =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Working...")

    if not tele_client.is_connected():
        await tele_client.connect()

    await tele_client.send_message(TARGET_BOT, "/start")
    await asyncio.sleep(2)
    await tele_client.send_message(TARGET_BOT, "/status https://t.me/examplegroup")

    await update.message.reply_text("📤 Sent. Waiting for response.")

# ===== MAIN ASYNC RUNNER =====
async def main():
    await tele_client.start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 Bot running (Python 3.13 SAFE)")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())