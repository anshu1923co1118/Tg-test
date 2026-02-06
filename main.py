import threading
import asyncio
import re
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

# last request kis user ne bheji, uska chat_id
last_request_chat_id: int | None = None

@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def target_listener(event):
    """
    IP bot ka pura result aayega; yahan se CMD: line cut karke
    last_request_chat_id wale user ko bhejna hai.
    """
    global last_request_chat_id
    text = event.text or ""
    print("📩 TARGET BOT REPLY:", text)

    if last_request_chat_id is None:
        return

    # CMD line nikaalo
    m = re.search(r"CMD:s*(.+)", text)
    if not m:
        return

    final_cmd = m.group(1)
    print("✅ FINAL CMD:", final_cmd)

    from telegram import Bot
    bot = Bot(BOT_TOKEN)
    await bot.send_message(
        chat_id=last_request_chat_id,
        text=f"✅ CMD:
`{final_cmd}`",
        parse_mode="Markdown"
    )

    # ek request complete ho gayi, next ke liye reset
    last_request_chat_id = None

def start_telethon():
    asyncio.run(run_telethon())

async def run_telethon():
    await tele_client.start()
    print("🧵 Telethon running")
    await tele_client.run_until_disconnected()

# -------- Telegram Bot (python-telegram-bot) --------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use:
"
        "/getip all <link_or_chatid>
"
        "Example:
"
        "/getip all https://t.me/Chatting_Groupc
"
        "/getip all -1002175729395"
    )

async def getip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /getip all <link_or_chatid>
    -> .getip all <link_or_chatid> target bot ko send
    -> reply se CMD: line user ko.
    """
    global last_request_chat_id

    if len(context.args) < 2 or context.args[0].lower() != "all":
        await update.message.reply_text(
            "Usage: /getip all <link_or_chatid>
"
            "Example:
"
            "/getip all https://t.me/Chatting_Groupc
"
            "/getip all -1002175729395"
        )
        return

    link_or_chatid = " ".join(context.args[1:]).strip()
    last_request_chat_id = update.effective_chat.id

    await update.message.reply_text("🚀 Sending to IP bot, wait for CMD…")

    async def send_to_target():
        if not tele_client.is_connected():
            await tele_client.connect()

        # bilkul waise hi jaise tum manually likhte ho:
        # .getip all <link_or_chatid>
        cmd = f".getip all {link_or_chatid}"
        await tele_client.send_message(TARGET_BOT, cmd)

    # Telethon ke apne loop me background task
    tele_client.loop.create_task(send_to_target())

def main():
    # Telethon ko background thread me chalao
    t = threading.Thread(target=start_telethon, daemon=True)
    t.start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("getip", getip_cmd))

    print("🤖 BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()