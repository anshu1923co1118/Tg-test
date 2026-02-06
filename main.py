import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"
TARGET_BOT = "@botbysahilbot"

STRING_SESSION = "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XNO1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2snpHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8vQoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="

# -------- Telethon client --------
tele_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# Store last requests per user (so multiple users can request simultaneously)
last_requests: dict[int, asyncio.Future] = {}


@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def target_listener(event):
    """
    Listens to the target bot responses and forwards CMD lines to the correct user.
    """
    text = event.text or ""
    print("📩 TARGET BOT REPLY:", text)

    # CMD line extraction
    m = re.search(r"CMD:\s*(.+)", text)
    if not m:
        return

    final_cmd = m.group(1)
    print("✅ FINAL CMD:", final_cmd)

    # Send CMD back to all pending users
    for chat_id, future in list(last_requests.items()):
        if not future.done():
            future.set_result(final_cmd)
        last_requests.pop(chat_id, None)


# -------- Telegram Bot (python-telegram-bot) --------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Use:
/getip all <link_or_chatid>
Example:
/getip all https://t.me/Chatting_Groupc
/getip all -1002175729395"""
    )


async def getip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /getip all <link_or_chatid>
    -> Sends `.getip all <link_or_chatid>` to the target bot
    -> Waits for CMD response and sends it back to user
    """
    if len(context.args) < 2 or context.args[0].lower() != "all":
        await update.message.reply_text(
            """Usage:
/getip all <link_or_chatid>
Example:
/getip all https://t.me/Chatting_Groupc
/getip all -1002175729395"""
        )
        return

    chat_id = update.effective_chat.id
    link_or_chatid = " ".join(context.args[1:]).strip()

    await update.message.reply_text("🚀 Sending to IP bot, wait for CMD…")

    # Create a Future to wait for the target bot's reply
    future = asyncio.get_event_loop().create_future()
    last_requests[chat_id] = future

    # Send command to target bot
    await tele_client.send_message(TARGET_BOT, f".getip all {link_or_chatid}")

    try:
        # Wait max 30s for reply
        final_cmd = await asyncio.wait_for(future, timeout=30)
        await update.message.reply_text(f"CMD:\n`{final_cmd}`", parse_mode="Markdown")
    except asyncio.TimeoutError:
        await update.message.reply_text("⚠️ Timeout: No response from target bot.")
        last_requests.pop(chat_id, None)


# -------- Main Async Entry --------
async def main():
    # Start Telethon client
    await tele_client.start()
    print("🧵 Telethon running")

    # Start Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("getip", getip_cmd))

    print("🤖 BOT RUNNING")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # keep running


if __name__ == "__main__":
    asyncio.run(main())