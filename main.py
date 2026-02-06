import threading
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"
TARGET_BOT = "@botbysahilbot"

STRING_SESSION = "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XNO1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2snpHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8vQoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="
# -------- Telethon client --------

tele_client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def target_listener(event):
    print("📩 TARGET BOT REPLY:", event.text)

def start_telethon():
    # Telethon apna khud ka event loop use karega is thread ke andar
    asyncio.run(run_telethon())

async def run_telethon():
    await tele_client.start()
    print("🧵 Telethon running")
    await tele_client.run_until_disconnected()

# -------- Telegram Bot (python-telegram-bot) --------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Working...")

    # Telethon se message bhejne ke liye uska loop use karna padega
    # isliye uska client direct await nahi karte, simple send karke chhod sakte ho
    if not tele_client.is_connected():
        await tele_client.connect()

    await tele_client.send_message(TARGET_BOT, "/start")
    await update.message.reply_text("📤 Sent to target bot")

def main():
    # Telethon ko background thread me chalao
    t = threading.Thread(target=start_telethon, daemon=True)
    t.start()

    # PTB normal sync run_polling (yahan apna loop manage karega)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 BOT RUNNING")
    app.run_polling()  # yahan koi asyncio.run ya await nahi

if __name__ == "__main__":
    main()