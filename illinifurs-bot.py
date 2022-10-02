#!/usr/bin/env python3
    
import os
import json
import asyncio
from plugins import fotorama

from telethon import TelegramClient

SECRET_FILE = os.path.expanduser("~/secrets/secret.json")

secrets = None
with open(SECRET_FILE, "r") as f:
    secrets = json.load(f)

async def main():
    async with (await TelegramClient("illinifurs_bot", secrets["tg-api-id"], secrets["tg-api-hash"]).start(bot_token=secrets["tg-bot-token"])) as bot:
        await fotorama.init(bot)
        await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
