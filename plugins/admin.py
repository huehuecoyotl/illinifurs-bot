import os
from telethon import Button, events

SITE_SCRIPT = os.path.expanduser("~/site/source/post_deploy.sh")
BOT_SCRIPT = os.path.expanduser("~/bot/post_deploy.sh")

async def adminTest(event, cur, callback=False):
	cur.execute("SELECT id FROM officers")
	admins = {adminId for (adminId,) in cur.fetchall()}
	sender = await event.get_sender()
	if sender.id in admins:
		return True
	else:
		text = "I'm sorry, but you are not authorized to access that function."
		buttons = []
		if callback:
			await event.edit(text, buttons=buttons)
		else:
			await event.respond(text)
		return False

async def admin_top_level(event, callback=False):
	text = "Which admin control would you like to access?"
	buttons = [
		[
			Button.inline("Fotorama", b'fotorama'),
			Button.inline("Officers", b'officers'),
			Button.inline("Events", b'events')
		], [
			Button.inline("Reload Site", b'reload:site'),
			Button.inline("Reload Bot", b'reload:bot')
		]
	]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def reloader_fn(event, which, scriptPath, callback=False):
	text = "Reloading %s!" % (which)
	buttons = [
		Button.inline("<< Back to admin menu.", b'admin')
	]
	cmd = "bash %s" % (scriptPath)

	if callback:
		await event.edit(text, buttons=buttons)
		os.system(cmd)
	else:
		await event.respond(text, buttons=buttons)
		os.system(cmd)

async def init(bot, cur, adminTest):
	@bot.on(events.NewMessage(pattern='/adminMenu'))
	async def handler(event):
		if await adminTest(event, cur):
			await admin_top_level(event)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'admin'))
	async def handler(event):
		if await adminTest(event, cur, True):
			await admin_top_level(event, True)
		raise events.StopPropagation

	@bot.on(events.NewMessage(pattern='/reloadSite'))
	async def handler(event):
		if await adminTest(event, cur):
			await reloader_fn(event, "site", SITE_SCRIPT)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'reload:site'))
	async def handler(event):
		if await adminTest(event, cur, True):
			await reloader_fn(event, "site", SITE_SCRIPT, True)
		raise events.StopPropagation

	@bot.on(events.NewMessage(pattern='/reloadBot'))
	async def handler(event):
		if await adminTest(event, cur):
			await reloader_fn(event, "bot", BOT_SCRIPT)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'reload:bot'))
	async def handler(event):
		if await adminTest(event, cur, True):
			await reloader_fn(event, "bot", BOT_SCRIPT, True)
		raise events.StopPropagation
