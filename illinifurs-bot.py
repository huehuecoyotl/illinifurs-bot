#!/usr/bin/env python3
    
import os
import json
import socket
import asyncio
import sqlite3
import mysql.connector
from plugins import fotorama, admin

from telethon import TelegramClient

SECRET_FILE = os.path.expanduser("~/secrets/secret.json")

secrets = None
with open(SECRET_FILE, "r") as f:
    secrets = json.load(f)

prodFlag = socket.gethostname() == "illinifurs.com"

con = None
cur = None
if prodFlag:
    con = mysql.connector.connect(host="localhost", user="illapp", password=secrets["website-mysql-pw"], database="website")
    cur = con.cursor()
else:
    con = sqlite3.connect("test.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fotorama (
            url TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            caption TEXT
        );""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            chatInviter INTEGER NOT NULL
        );""")
    cur.execute("""
        INSERT INTO officers
            (id, title, chatInviter)
            VALUES
            (154194108, 'admin', 1);
        """)
    con.commit()

async def main():
    async with (await TelegramClient("illinifurs_bot", secrets["tg-api-id"], secrets["tg-api-hash"]).start(bot_token=secrets["tg-bot-token"])) as bot:
        await fotorama.init(bot, prodFlag, con, cur, admin.adminTest)
        await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
