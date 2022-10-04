import re
import hashlib
from enum import Enum, auto
from telethon import Button, events

# We use a Python Enum for the state because it's a clean and easy way to do it
class FotoramaState(Enum):
	FOTO_ADD_IMAGE = auto()
	FOTO_ADD_VIDEO = auto()
	FOTO_ADD_CAPTION = auto()
	FOTO_EDIT_URL = auto()
	FOTO_EDIT_CAPTION = auto()

# The state in which different users are, {user_id: state}
fotorama_state = {}
fotorama_data = {}
url_hashes = {}

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

async def add_fotorama_image_to_db(event, prodFlag, con, cur, url, fotoramaType, caption=None):
	who = event.sender_id
	if who in fotorama_state:
		del fotorama_state[who]
	if who in fotorama_data:
		del fotorama_data[who]

	query1 = ""
	query2 = ""
	if caption is None:
		if prodFlag:
			query1 = "UPDATE fotorama SET type=%s WHERE url=%s"
			query2 = "INSERT INTO fotorama (url, type) VALUES (%s, %s)" 
		else:
			query1 = "UPDATE fotorama SET type=? WHERE url=?"
			query2 = "INSERT INTO fotorama (url, type) VALUES (?, ?)"
		cur.execute(query1, (fotoramaType, url))
		cur.execute(query2, (url, fotoramaType))
		con.commit()
	else:
		if prodFlag:
			query1 = "UPDATE fotorama SET type=%s, caption=%s WHERE url=%s"
			query2 = "INSERT INTO fotorama (url, type, caption) VALUES (%s, %s, %s)" 
		else:
			query1 = "UPDATE fotorama SET type=?, caption=? WHERE url=?"
			query2 = "INSERT INTO fotorama (url, type, caption) VALUES (?, ?, ?)"
		cur.execute(query1, (fotoramaType, caption, url))
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
	query = ""
	queryVars = None
	if newURL is not None:
		if prodFlag:
			query = "UPDATE fotorama SET url=%s WHERE url=%s"
		else:
			query = "UPDATE fotorama SET url=? WHERE url=?"
		queryVars = (newURL, oldURL)
	elif fotoramaType is not None:
		if prodFlag:
			query = "UPDATE fotorama SET type=%s WHERE url=%s"
		else:
			query = "UPDATE fotorama SET type=? WHERE url=?"
		queryVars = (fotoramaType, oldURL)
	elif caption is not None:
		if prodFlag:
			query = "UPDATE fotorama SET caption=%s WHERE url=%s"
		else:
			query = "UPDATE fotorama SET caption=? WHERE url=?"
		queryVars = (caption, oldURL)
	if queryVars is not None:
		cur.execute(query, queryVars)
		con.commit()

def remove_caption_from_fotorama_image(prodFlag, con, cur, url):
	query = ""
	if prodFlag:
		query = "UPDATE fotorama SET caption=NULL WHERE url=%s"
	else:
		query = "UPDATE fotorama SET caption=NULL WHERE url=?"
	cur.execute(query, (url,))
	con.commit()

def remove_fotorama_image_from_db(prodFlag, con, cur, url):
	query = ""
	if prodFlag:
		query = "DELETE FROM fotorama WHERE url=%s"
	else:
		query = "DELETE FROM fotorama WHERE url=?"
	cur.execute(query, (url,))
	con.commit()

async def fotorama_top_level(event, callback=False):
	who = event.sender_id
	if who in fotorama_state:
		del fotorama_state[who]
	if who in fotorama_data:
		del fotorama_data[who]

	text = "What would you like to do with the fotorama settings?"
	buttons = [
		Button.inline("Add a new item.", b'fotorama:add'),
		Button.inline("Remove an item.", b'fotorama:remove'),
		Button.inline("Edit an item.", b'fotorama:edit')
	]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def init(bot, prodFlag, con, cur, adminTest):
	@bot.on(events.NewMessage(pattern='/fotorama'))
	async def handler(event):
		if adminTest(event, cur):
			await fotorama_top_level(event)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'fotorama'))
	async def handler(event):
		if adminTest(event, cur):
			await fotorama_top_level(event, True)

	@bot.on(events.CallbackQuery(data=b'fotorama:add'))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			if who in fotorama_state:
				del fotorama_state[who]
			if who in fotorama_data:
				del fotorama_data[who]

			text = "Will this item be an image, or a video?"
			buttons = [
				[
					Button.inline("Image", b'fotorama:add:image'),
					Button.inline("Video", b'fotorama:add:video')
				],
				[Button.inline("<< Back to fotorama menu", b'fotorama')]
			]

			await event.edit(text, buttons=buttons)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:(image|video)')))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			text = "Ok, tell me the URL of the item you want to add."
			fotoramaType = event.data_match[1].decode('utf8')

			if fotoramaType == "image":
				fotorama_state[who] = FotoramaState.FOTO_ADD_IMAGE
			else:
				fotorama_state[who] = FotoramaState.FOTO_ADD_VIDEO

			await event.respond(text)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:yes')))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			text = "Ok, tell me the caption for the item you want to add."
			fotorama_state[who] = FotoramaState.FOTO_ADD_CAPTION
			await event.respond(text)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:add:no')))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			data = fotorama_data.get(who)
			await add_fotorama_image_to_db(event, prodFlag, con, cur, data.get('url'), data.get('type'))

	@bot.on(events.CallbackQuery(data=b'fotorama:remove'))
	async def handler(event):
		if adminTest(event, cur):
			text = "Which item would you like to remove?"
			urls = retrieve_fotorama_images_from_db(prodFlag, cur)
			for (url,) in urls:
				url_hashes[hashlib.sha256(url.encode()).hexdigest()[:16]] = url
			buttons = [ [Button.inline(url, bytes("fotorama:remove:%s" % urlHash, encoding="utf8"))] for urlHash, url in url_hashes.items() ]
			buttons.append([Button.inline("<< Back to fotorama menu", b'fotorama')])
			await event.edit(text, buttons=buttons)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:remove:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			urlHash = event.data_match[1].decode('utf8')
			url = url_hashes.get(urlHash)
			remove_fotorama_image_from_db(prodFlag, con, cur, url)
			text = "Item with url %s removed from DB! Would you like to remove another item?" % url
			buttons = [
				Button.inline("Remove another item", b'fotorama:remove'),
				Button.inline("<< Back to fotorama menu", b'fotorama')
			]
			
			await event.edit(text, buttons=buttons)

	@bot.on(events.CallbackQuery(data=b'fotorama:edit'))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			if who in fotorama_state:
				del fotorama_state[who]
			if who in fotorama_data:
				del fotorama_data[who]

			text = "Which item would you like to edit?"
			urls = retrieve_fotorama_images_from_db(cur)
			for (url,) in urls:
				url_hashes[hashlib.sha256(url.encode()).hexdigest()[:16]] = url
			buttons = [ [Button.inline(url, bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8"))] for urlHash, url in url_hashes.items()]
			buttons.append([Button.inline("<< Back to fotorama menu", b'fotorama')])
			await event.edit(text, buttons=buttons)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:gen:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			urlHash = event.data_match[1].decode('utf8')
			url = url_hashes.get(urlHash)
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

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:url:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			urlHash = event.data_match[1].decode('utf8')
			url = url_hashes.get(urlHash)
			fotorama_state[who] = FotoramaState.FOTO_EDIT_URL
			fotorama_data[who] = {"url": url}
			text = "Ok, tell me the new URL for this item."
			await event.respond(text)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:type:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
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

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:(image|video):(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			fotoramaType = event.data_match[1].decode('utf8')
			urlHash = event.data_match[2].decode('utf8')
			url = url_hashes.get(urlHash)

			edit_fotorama_image_in_db(prodFlag, con, cur, url, fotoramaType=fotoramaType)

			text = "Success! Item updated."
			buttons = [
				Button.inline("Continue editing", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8")),
				Button.inline("<< Back to URL list", b'fotorama:edit')
			]
			await event.edit(text, buttons=buttons)


	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:caption:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			urlHash = event.data_match[1].decode('utf8')
			url = url_hashes.get(urlHash)
			fotorama_state[who] = FotoramaState.FOTO_EDIT_CAPTION
			fotorama_data[who] = {"url": url}
			text = "Ok, tell me the new caption for this item."
			await event.respond(text)

	@bot.on(events.CallbackQuery(data=re.compile(b'fotorama:edit:remove:caption:(.*)')))
	async def handler(event):
		if adminTest(event, cur):
			urlHash = event.data_match[1].decode('utf8')
			url = url_hashes.get(urlHash)
			remove_caption_from_fotorama_image(prodFlag, con, cur, url)
			text = "Success! Item updated."
			buttons = [
				Button.inline("Continue editing", bytes("fotorama:edit:gen:%s" % urlHash, encoding="utf8")),
				Button.inline("<< Back to URL list", b'fotorama:edit')
			]
			await event.edit(text, buttons=buttons)

	@bot.on(events.NewMessage)
	async def handler(event):
		if adminTest(event, cur):
			who = event.sender_id
			state = fotorama_state.get(who)

			if state is None:
				return

			elif (state == FotoramaState.FOTO_ADD_IMAGE or state == FotoramaState.FOTO_ADD_VIDEO):
				text = "Would you like to add a caption for this item?"
				buttons = [
					[
						Button.inline("Yes", b'fotorama:add:yes'),
						Button.inline("No", b'fotorama:add:no')
					],
					[Button.inline("Cancel", b'fotorama:add')]
				]

				data = None
				if state == FotoramaState.FOTO_ADD_IMAGE:
					data = {
						"url": event.text,
						"type": "image"
					}
					if who in fotorama_state:
						del fotorama_state[who]
					fotorama_data[who] = data
				else:
					data = {
						"url": event.text,
						"type": "video"
					}
					if who in fotorama_state:
						del fotorama_state[who]
					fotorama_data[who] = data
				
				await event.respond(text, buttons=buttons)
				raise events.StopPropagation

			elif state == FotoramaState.FOTO_ADD_CAPTION:
				data = fotorama_data.get(who)
				caption = event.text
				await add_fotorama_image_to_db(event, prodFlag, con, cur, data.get('url'), data.get('type'), caption)
				raise events.StopPropagation

			elif (state == FotoramaState.FOTO_EDIT_URL or state == FotoramaState.FOTO_EDIT_CAPTION):
				data = fotorama_data.get(who)
				url = data.get('url')

				if who in fotorama_state:
					del fotorama_state[who]
				if who in fotorama_data:
					del fotorama_data[who]

				text = "Success! Item updated."
				update = event.text

				if state == FotoramaState.FOTO_EDIT_URL:
					edit_fotorama_image_in_db(prodFlag, con, cur, url, newURL=update)
				else:
					edit_fotorama_image_in_db(prodFlag, con, cur, url, caption=update)

				await event.respond(text)