import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"
TARGET_BOT = "@botbysahilbot"

STRING_SESSION = "1BVtsOKEBu73mh4SW00pWPqOS8h6p4Gk6bVtQ5bgBPMaR645jIhARGSfzkmyEQEYhOAh2AEv8mq9EZL86Zd95StVzPwWaQLNl-EbOp5fVVeFK_ZUuN93mEZFMEuF7o6LCMgbJwvgVQuWQdycOnB652OY_zzZvOLcOPxWuLQOvLIuwtoYpNvL3Qs_PfGGHNAojo7k-NgMFURnj_UP0rh7RRDvAWN7lT1_jzma5dn7HhkPgsrwSieDtgqBkDftRxZQc9FYG2iYmyoJarEhfrqn3UbrueWqN0XiO983MRg-EavUGFWPNQ4QnQgUEf-uptcaeroorCOBv0gCfr3DjpFv4oLrG-SHkrFA="

# ---------- Telethon client ----------

tele_client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def target_listener(event):
    print("📩 TARGET BOT REPLY:", event.text)

# ---------- Telegram Bot (python-telegram-bot) ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Working...")

    if not tele_client.is_connected():
        await tele_client.connect()

    await tele_client.send_message(TARGET_BOT, "/start")
    await update.message.reply_text("📤 Sent to target bot")

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 BOT RUNNING")
    # IMPORTANT: no await here; this manages its own loop
    app.run_polling()

async def main():
    # Start Telethon client in this event loop
    await tele_client.start()

    # Now hand over control to PTB's own loop
    run_bot()

if __name__ == "__main__":
    asyncio.run(main())