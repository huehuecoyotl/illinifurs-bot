import re
import hashlib
from telethon import Button, events

urlHashes = {}

def retrieve_fotorama_images_from_db(prodFlag, cur, url=None):
	if url is None:
		cur.execute("SELECT url FROM fotorama")
		return cur.fetchall()
	else:
		query = ""
		if prodFlag:
			query = "SELECT * FROM fotorama WHERE url=%s"
		else:
			query = "SELECT * FROM fotorama WHERE url=?"
		cur.execute(query, (url,))
		retval = cur.fetchall()
		if len(retval) == 0:
			return None
		return retval[0]

async def add_fotorama_image_to_db(event, prodFlag, con, cur, conversationState, conversationData, url, fotoramaType, caption=None):
	sender = await event.get_sender()
	who = sender.id
	if who in conversationState:
		del conversationState[who]
	if who in conversationData:
		del conversationData[who]

	query1 = ""
	query2 = ""
	if prodFlag:
		query1 = "DELETE FROM fotorama WHERE url=%s"
		query2 = "INSERT INTO fotorama (url, type, caption) VALUES (%s, %s, %s)" 
	else:
		query1 = "DELETE FROM fotorama WHERE url=?"
		query2 = "INSERT INTO fotorama (url, type, caption) VALUES (?, ?, ?)"
	cur.execute(query1, (url,))
	cur.execute(query2, (url, fotoramaType, caption))
	con.commit()

	text = "Item added to database!"
	buttons = [
		[Button.inline("Add another item", b'fotorama:add')],
		[Button.inline("<< Back to fotorama menu", b'fotorama')]
	]
	if caption is None:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

def edit_fotorama_image_in_db(prodFlag, con, cur, oldURL, newURL=None, fotoramaType=None, caption=None):
	if newURL is not None:
		real_edit_fotorama_image_in_db(prodFlag, con, cur, oldURL, "url", newURL)
	if fotoramaType is not None:
		real_edit_fotorama_image_in_db(prodFlag, con, cur, oldURL, "type", fotoramaType)
	if caption is not None:
		real_edit_fotorama_image_in_db(prodFlag, con, cur, oldURL, "caption", caption)

def real_edit_fotorama_image_in_db(prodFlag, con, cur, oldURL, which, data):
	query = ""
	queryVars = (data, oldURL)
	if prodFlag:
		query = "UPDATE fotorama SET %s=%%s WHERE url=%%s" % (which)
	else:
		query = "UPDATE fotorama SET %s=? WHERE url=?" % (which)
	cur.execute(query, queryVars)
	con.commit()

def remove_caption_from_fotorama_image(prodFlag, con, cur, url):
	real_edit_fotorama_image_in_db(prodFlag, con, cur, url, "caption", None)

def remove_fotorama_image_from_db(prodFlag, con, cur, url):
	query = ""
	if prodFlag:
		query = "DELETE FROM fotorama WHERE url=%s"
	else:
		query = "DELETE FROM fotorama WHERE url=?"
	cur.execute(query, (url,))
	con.commit()

async def fotorama_top_level(event, conversationState, conversationData, callback=False):
	sender = await event.get_sender()
	who = sender.id
	if who in conversationState:
		del conversationState[who]
	if who in conversationData:
		del conversationData[who]

	text = "What would you like to do with the fotorama settings?"
	buttons = [
		[
			Button.inline("Add a new item.", b'fotorama:add'),
			Button.inline("Remove an item.", b'fotorama:remove'),
			Button.inline("Edit an item.", b'fotorama:edit')
		], [
			Button.inline("<< Back to admin menu.", b'admin')
		]
	]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, adminTest):
	@bot.on(events.NewMessage(pattern='/fotoramaMenu'))
	async def handler(event):
		if await adminTest(event, cur):
			await fotorama_top_level(event, conversationState, conversationData)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'fotorama'))
	async def handler(event):
		if await adminTest(event, cur, True):
			await fotorama_top_level(event, conversationState, conversationData, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'fotorama:add'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			text = "Will this item be an image, or a video?"
			buttons = [
				[
					Button.inline("Image", b'fotorama:add:image'),
					Button.inline("Video", b'fotorama:add:video')
				],
				[Button.inline("<< Back to fotorama menu", b'fotorama')]
			]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:(image|video)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			text = "Ok, tell me the URL of the item you want to add."
			buttons = [Button.inline("Cancel", b'fotorama:add')]
			fotoramaType = event.data_match[1].decode('utf8')

			if fotoramaType == "image":
				conversationState[who] = IlliniFursState.FOTO_ADD_IMAGE
			else:
				conversationState[who] = IlliniFursState.FOTO_ADD_VIDEO

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:yes')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			text = "Ok, tell me the caption for the item you want to add."
			buttons = [Button.inline("Cancel", b'fotorama:add')]
			conversationState[who] = IlliniFursState.FOTO_ADD_CAPTION
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:no')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			data = conversationData.get(who)
			await add_fotorama_image_to_db(event, prodFlag, con, cur, conversationState, conversationData, data.get('url'), data.get('type'))
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'fotorama:remove'))
	async def handler(event):
		if await adminTest(event, cur, True):
			text = "Which item would you like to remove?"
			urls = retrieve_fotorama_images_from_db(prodFlag, cur)
			for (url,) in urls:
				urlHashes[hashlib.sha256(url.encode()).hexdigest()[:16]] = url
			buttons = [ [Button.inline(url, bytes("fotorama:remove:%s" % urlHash, encoding="utf8"))] for urlHash, url in urlHashes.items() ]
			buttons.append([Button.inline("<< Back to fotorama menu", b'fotorama')])
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:remove:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			urlHash = event.data_match[1].decode('utf8')
			url = urlHashes.get(urlHash)
			del urlHashes[urlHash]
			remove_fotorama_image_from_db(prodFlag, con, cur, url)
			text = "Item with url %s removed from DB! Would you like to remove another item?" % url
			buttons = [
				Button.inline("Remove another item", b'fotorama:remove'),
				Button.inline("<< Back to fotorama menu", b'fotorama')
			]
			
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'fotorama:edit'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			text = "Which item would you like to edit?"
			urls = retrieve_fotorama_images_from_db(prodFlag, cur)
			for (url,) in urls:
				urlHashes[hashlib.sha256(url.encode()).hexdigest()[:16]] = url
			buttons = [ [Button.inline(url, bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8"))] for urlHash, url in urlHashes.items()]
			buttons.append([Button.inline("<< Back to fotorama menu", b'fotorama')])
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:gen:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			urlHash = event.data_match[1].decode('utf8')
			url = urlHashes.get(urlHash)
			(url, fotoramaType, caption) = retrieve_fotorama_images_from_db(prodFlag, cur, url)
			text = """Editing info for fotorama item.

URL: %s
Type: %s
Caption: %s""" % (url, fotoramaType, caption)
			buttons = [
				[
					Button.inline("Edit URL", bytes("fotorama:edit:url:%s" % urlHash, encoding="utf8")),
					Button.inline("Edit Type", bytes("fotorama:edit:type:%s" % urlHash, encoding="utf8"))
				], [
					Button.inline("Edit Caption", bytes("fotorama:edit:caption:%s" % urlHash, encoding="utf8")),
					Button.inline("Remove Caption", bytes("fotorama:edit:remove:caption:%s" % urlHash, encoding="utf8"))
				],
				[Button.inline("<< Back to URL list", b'fotorama:edit')]
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:url:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			urlHash = event.data_match[1].decode('utf8')
			url = urlHashes.get(urlHash)
			conversationState[who] = IlliniFursState.FOTO_EDIT_URL
			conversationData[who] = {"url": url}
			text = "Ok, tell me the new URL for this item."
			buttons = [Button.inline("Cancel", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8"))]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:type:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			urlHash = event.data_match[1].decode('utf8')
			text = "Is this an image or a video?"
			buttons = [
				[
					Button.inline("Image", bytes("fotorama:edit:image:%s" % urlHash, encoding="utf8")),
					Button.inline("Video", bytes("fotorama:edit:video:%s" % urlHash, encoding="utf8"))
				],
				[Button.inline("Cancel", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8"))]
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:(image|video):(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			fotoramaType = event.data_match[1].decode('utf8')
			urlHash = event.data_match[2].decode('utf8')
			url = urlHashes.get(urlHash)

			edit_fotorama_image_in_db(prodFlag, con, cur, url, fotoramaType=fotoramaType)

			text = "Success! Item updated."
			buttons = [
				Button.inline("Continue editing", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8")),
				Button.inline("<< Back to URL list", b'fotorama:edit')
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:caption:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			urlHash = event.data_match[1].decode('utf8')
			url = urlHashes.get(urlHash)
			conversationState[who] = IlliniFursState.FOTO_EDIT_CAPTION
			conversationData[who] = {"url": url}
			text = "Ok, tell me the new caption for this item."
			buttons = [Button.inline("Cancel", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8"))]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:remove:caption:(.*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			urlHash = event.data_match[1].decode('utf8')
			url = urlHashes.get(urlHash)

			remove_caption_from_fotorama_image(prodFlag, con, cur, url)
			text = "Success! Item updated."
			buttons = [
				Button.inline("Continue editing", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8")),
				Button.inline("<< Back to URL list", b'fotorama:edit')
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.NewMessage)
	async def handler(event):
		sender = await event.get_sender()
		who = sender.id
		state = conversationState.get(who)

		if state is None:
			return

		if (state == IlliniFursState.FOTO_ADD_IMAGE or state == IlliniFursState.FOTO_ADD_VIDEO):
			if await adminTest(event, cur):
				text = "Would you like to add a caption for this item?"
				buttons = [
					[
						Button.inline("Yes", b'fotorama:add:yes'),
						Button.inline("No", b'fotorama:add:no')
					],
					[Button.inline("Cancel", b'fotorama:add')]
				]

				data = None
				if state == IlliniFursState.FOTO_ADD_IMAGE:
					data = {
						"url": event.text,
						"type": "image"
					}
					if who in conversationState:
						del conversationState[who]
					conversationData[who] = data
				else:
					data = {
						"url": event.text,
						"type": "video"
					}
					if who in conversationState:
						del conversationState[who]
					conversationData[who] = data
				
				await event.respond(text, buttons=buttons)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		elif state == IlliniFursState.FOTO_ADD_CAPTION:
			if await adminTest(event, cur):
				data = conversationData.get(who)
				caption = event.text
				await add_fotorama_image_to_db(event, prodFlag, con, cur, conversationState, conversationData, data.get('url'), data.get('type'), caption)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		elif (state == IlliniFursState.FOTO_EDIT_URL or state == IlliniFursState.FOTO_EDIT_CAPTION):
			if await adminTest(event, cur):
				data = conversationData.get(who)
				url = data.get('url')
				urlHash = hashlib.sha256(url.encode()).hexdigest()[:16]

				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]

				text = "Success! Item updated."
				update = event.text

				if state == IlliniFursState.FOTO_EDIT_URL:
					edit_fotorama_image_in_db(prodFlag, con, cur, url, newURL=update)
					del urlHashes[urlHash]
					urlHash = hashlib.sha256(update.encode()).hexdigest()[:16]
					urlHashes[urlHash] = update
				else:
					edit_fotorama_image_in_db(prodFlag, con, cur, url, caption=update)

				buttons = [
					Button.inline("Continue editing", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8")),
					Button.inline("<< Back to URL list", b'fotorama:edit')
				]

				await event.respond(text, buttons=buttons)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation
