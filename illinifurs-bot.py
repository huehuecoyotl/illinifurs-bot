#!/usr/bin/env python3
	
import os
import json
import socket
import asyncio
import sqlite3
import logging
import mysql.connector
from enum import Enum, auto
from plugins import fotorama, officers, admin, events
from telethon import TelegramClient

logging.basicConfig(filename='illinifurs-bot.log', filemode='a', format='Bot - %(levelname)s - %(message)s', level=logging.WARNING)

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
			username TEXT NOT NULL,
			displayName TEXT,
			title TEXT NOT NULL,
			imageURL TEXT NOT NULL,
			chatInviter INTEGER NOT NULL
		);""")
	cur.execute("""
		CREATE TABLE IF NOT EXISTS events (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			location TEXT NOT NULL,
			start TEXT NOT NULL,
			end TEXT NOT NULL,
			allDay INTEGER NOT NULL,
			description TEXT NOT NULL
		);""")
	# You'll need to find your telegram id and add it here to test admin bot commands
	cur.execute("""
		INSERT OR REPLACE INTO officers
			(id, username, displayName, title, imageURL, chatInviter)
			VALUES
			(154194108, 'stanthreetimes', 'Stanford Stills', 'site-admin', 'https://coyo.tl/images/profile.png', 1);
		""")
	cur.execute("""
		INSERT OR REPLACE INTO events
			(id, name, location, start, end, allDay, description)
			VALUES
			(1, 'Test', 'Urbana', '2022-10-15 17:00:00', '2022-10-16 19:00:00', 0, 'Test Event'),
			(2, 'Long Title Splits Over Many Lines', 'Champaign', '2022-10-22 17:00:00', '2022-10-22 19:00:00', 1, 'Other Event https://coyo.tl/');
		""")
	con.commit()

# We use a Python Enum for the state because it's a clean and easy way to do it
class IlliniFursState(Enum):
	FOTO_ADD_IMAGE = auto()
	FOTO_ADD_VIDEO = auto()
	FOTO_ADD_CAPTION = auto()
	FOTO_EDIT_URL = auto()
	FOTO_EDIT_CAPTION = auto()
	OFFICER_ADD = auto()
	EVENT_ADD_NAME = auto()
	EVENT_ADD_LOCATION = auto()
	EVENT_ADD_DESCRIPTION = auto()
	EVENT_EDIT_NAME = auto()
	EVENT_EDIT_LOCATION = auto()
	EVENT_EDIT_DESCRIPTION = auto()

# The state in which different users are, {user_id: state}
conversationState = {}
conversationData = {}

async def main():
	async with (await TelegramClient("illinifurs_bot", secrets["tg-api-id"], secrets["tg-api-hash"]).start(bot_token=secrets["tg-bot-token"])) as bot:
		await admin.init(bot, cur, admin.adminTest)
		await fotorama.init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, admin.adminTest)
		await officers.init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, admin.adminTest)
		await events.init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, admin.adminTest)
		await bot.run_until_disconnected()

if __name__ == '__main__':
	asyncio.run(main())
