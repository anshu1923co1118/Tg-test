from telethon import TelegramClient, events
import asyncio
import re
import sys

# ===== CONFIG =====
API_ID = 36295148
API_HASH = "bee66be844e3be0e314508e92a7c4e7d"
TARGET_BOT = "@example_bot"   # yahan target bot ka username
# ==================

client = TelegramClient("session_final", API_ID, API_HASH)

@client.on(events.NewMessage(from_users=TARGET_BOT))
async def handle_response(event):
    text = event.text or ""

    match = re.search(r"CMD:\s*(.+)", text)
    if match:
        final_cmd = match.group(1)

        print("✅ FINAL RESPONSE:")
        print(final_cmd)

        # optional: save
        with open("output.txt", "w") as f:
            f.write(final_cmd)

        # kaam ho gaya → exit
        await client.disconnect()


async def main():
    if len(sys.argv) < 2 or sys.argv[1] != "start":
        print("Use: python bot.py start")
        return

    await client.start()
    print("✅ Bot started")

    # step 1: start target bot
    await client.send_message(TARGET_BOT, "/start")
    await asyncio.sleep(2)

    # step 2: input command (placeholder)
    await client.send_message(
        TARGET_BOT,
        "/status https://t.me/examplegroup"
    )

    print("📤 Input sent, waiting for response...")


with client:
    client.loop.run_until_complete(main())