import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

# ===== BOT CONFIG =====
BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"

# ===== TELETHON LISTENER =====
@tele_client.on(events.NewMessage(from_users=TARGET_BOT))
async def handle_target_response(event):
    print("📩 RAW RESPONSE:", event.text)

    match = re.search(r"CMD:\s*(.+)", event.text or "")
    if match:
        final_cmd = match.group(1)

        print("✅ FINAL COMMAND:", final_cmd)

        with open("output.txt", "w") as f:
            f.write(final_cmd)

# ===== BOT COMMAND =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Processing…")

    if not tele_client.is_connected():
        await tele_client.connect()

    await tele_client.send_message(TARGET_BOT, "/start")
    await asyncio.sleep(2)

    await tele_client.send_message(
        TARGET_BOT,
        "/status https://t.me/examplegroup"
    )

    await update.message.reply_text("📤 Command sent, waiting for response…")

# ===== MAIN =====
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(tele_client.connect())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))

    print("🤖 Bot + Telethon running (HARDCODED STRING SESSION)")
    app.run_polling()

if __name__ == "__main__":
    main()