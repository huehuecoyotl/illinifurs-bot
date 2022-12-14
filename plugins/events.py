import re
import datetime
import calendar
from telethon import Button, events

def retrieve_event_from_db(prodFlag, cur, eventId=None):
	if eventId is None:
		cur.execute("SELECT id, name, start FROM events ORDER BY start")
		return cur.fetchall()
	else:
		query = ""
		if prodFlag:
			query = "SELECT name, location, start, end, allDay, description FROM events WHERE id=%s"
		else:
			query = "SELECT name, location, start, end, allDay, description FROM events WHERE id=?"
		cur.execute(query, (eventId,))
		retval = cur.fetchall()
		if len(retval) == 0:
			return None
		(name, location, start, end, allDay, description) = retval[0]
		if not prodFlag:
			start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
			end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
		return (name, location, start, end, allDay, description)

def retrieve_all_events_from_db(prodFlag, cur):
	query = "SELECT name, location, start, end, allDay, description FROM events ORDER BY start"
	cur.execute(query)
	retval = []
	if prodFlag:
		retval = cur.fetchall()
	else:
		retval = [(name, location, datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S"), datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S"), allDay, description) for (name, location, start, end, allDay, description) in cur.fetchall()]
	return retval

def retrieve_weekly_from_db(prodFlag, cur):
	query = "SELECT name, location, startTime, endTime, dayOfWeek, description FROM weekly_meeting"
	cur.execute(query)
	(name, location, startTime, endTime, dayOfWeek, description) = cur.fetchall()[0]
	if not prodFlag:
		startTime = datetime.datetime.strptime(startTime, "%H:%M:%S")
		endTime = datetime.datetime.strptime(endTime, "%H:%M:%S")
	return (name, location, startTime, endTime, dayOfWeek, description)

def retrieve_announce_channel_from_db(prodFlag, cur):
	query = "SELECT id FROM announce_channel"
	cur.execute(query)
	return cur.fetchall()[0]

def add_event_to_db(prodFlag, con, cur, name, location, start, end, allDay, description):
	query = ""
	queryVars = (name, location, start, end, allDay, description)
	if prodFlag:
		query = "INSERT INTO events (name, location, start, end, allDay, description) VALUES (%s, %s, %s, %s, %s, %s)"
	else:
		query = "INSERT INTO events (name, location, start, end, allDay, description) VALUES (?, ?, ?, ?, ?, ?)"
	cur.execute(query, queryVars)
	con.commit()

def update_event_in_db(prodFlag, con, cur, eventId, name=None, location=None, start=None, end=None, allDay=None, description=None):
	if name is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "name", name)
	if location is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "location", location)
	if start is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "start", start)
	if end is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "end", end)
	if allDay is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "allDay", allDay)
	if description is not None:
		real_update_event_in_db(prodFlag, con, cur, eventId, "description", description)

def real_update_event_in_db(prodFlag, con, cur, eventId, which, data):
	query = ""
	queryVars = (data, eventId)
	if prodFlag:
		query = "UPDATE events SET %s=%%s WHERE id=%%s" % (which)
	else:
		query = "UPDATE events SET %s=? WHERE id=?" % (which)
	cur.execute(query, queryVars)
	con.commit()

def update_weekly_in_db(prodFlag, con, cur, name=None, location=None, startTime=None, endTime=None, dayOfWeek=None, description=None):
	if name is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "name", name)
	if location is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "location", location)
	if startTime is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "startTime", startTime)
	if endTime is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "endTime", endTime)
	if dayOfWeek is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "dayOfWeek", dayOfWeek)
	if description is not None:
		real_update_weekly_in_db(prodFlag, con, cur, "description", description)

def real_update_weekly_in_db(prodFlag, con, cur, which, data):
	query = ""
	if prodFlag:
		query = "UPDATE weekly_meeting SET %s=%%s" % (which)
	else:
		query = "UPDATE weekly_meeting SET %s=?" % (which)
	cur.execute(query, (data,))
	con.commit()

def remove_event_from_db(prodFlag, con, cur, eventId):
	query = ""
	if prodFlag:
		query = "DELETE FROM events WHERE id=%s"
	else:
		query = "DELETE FROM events WHERE id=?"
	cur.execute(query, (eventId,))
	con.commit()

def getDepth(time1, time2):
	depth1 = (0 if time1.minute == 0 else 1) if time1.second == 0 else 2
	depth2 = (0 if time2.minute == 0 else 1) if time2.second == 0 else 2
	return max(depth1, depth2)

def getDifferentMeridian(time1, time2):
	meridian1 = time1.hour < 12;
	meridian2 = time2.hour < 12;
	retval = meridian1 != meridian2;
	return (retval or time1.hour % 12 == 0 or time2.hour % 12 == 0);

def getWhen(start, end, allDay):
	now = datetime.datetime.now()
	compareData = [
		start.year == end.year,
		start.month == end.month,
		start.day == end.day,
		start.hour == end.hour,
		start.minute == end.minute,
		start.second == end.second
	]

	i = 0;
	while (compareData[i]):
		i = i + 1

	depth = getDepth(start, end)

	startStr = "???"
	endStr = "???"

	if i < 3:
		if allDay:
			startStr = start.strftime("%A, %B %-d, %Y")
			endStr = end.strftime("%A, %B %-d, %Y")
		else:
			formatStr = ""
			if depth == 0:
				formatStr = "%A, %B %-d, %Y %-I %p"
			elif depth == 1:
				formatStr = "%A, %B %-d, %Y %-I:%M %p"
			else:
				formatStr = "%A, %B %-d, %Y %-I:%M:%S %p"
			startStr = start.strftime(formatStr)
			endStr = end.strftime(formatStr)
	else:
		if allDay:
			return start.strftime("%A, %B %-d, %Y");
		useAMPM = getDifferentMeridian(start, end)
		startFormatStr = ""
		endFormatStr = ""
		if depth == 0:
			startFormatStr = "%A, %B %-d, %Y %-I %p" if useAMPM else "%A, %B %-d, %Y %-I"
			endFormatStr = "%-I %p"
		elif depth == 1:
			startFormatStr = "%A, %B %-d, %Y %-I:%M %p" if useAMPM else "%A, %B %-d, %Y %-I:%M"
			endFormatStr = "%-I:%M %p"
		else:
			startFormatStr = "%A, %B %-d, %Y %-I:%M:%S %p" if useAMPM else "%A, %B %-d, %Y %-I:%M:%S"
			endFormatStr = "%-I:%M:%S %p"
		startStr = start.strftime(startFormatStr)
		endStr = end.strftime(endFormatStr)

	return startStr + " -- " + endStr

def create_calendar_callback_data(bigAction, smallAction, year, month, day=None):
	if day is None:
		return bytes(":".join([bigAction, smallAction, str(year), str(month)]), encoding='utf8')
	else:
		return bytes(":".join([bigAction, smallAction, str(year), str(month), str(day)]), encoding='utf8')

def create_calendar(bigAction, year=None, month=None):
	cal = calendar.Calendar(firstweekday=6)
	now = datetime.datetime.now()
	if year is None:
		year = now.year
	if month is None:
		month = now.month

	data_ignore = create_calendar_callback_data(bigAction, "continue", year, month)
	keyboard = []

	# First row - Month and Year
	row = [
		Button.inline(calendar.month_name[month] + " " + str(year), data_ignore)
	]
	keyboard.append(row)

	# Second row - Week Days
	row = []
	for day in ["U", "M", "T", "W", "R", "F", "S"]:
		row.append(Button.inline(day, data_ignore))
	keyboard.append(row)

	currMonth = cal.monthdayscalendar(year, month)
	for week in currMonth:
		row = []
		for day in week:
			if (day == 0):
				row.append(Button.inline(" ", data_ignore))
			else:
				row.append(Button.inline(str(day), create_calendar_callback_data(bigAction, "select", year, month, day)))
		keyboard.append(row)

	# Last rows - Buttons
	prevMonth = 12 if month == 1 else month - 1
	prevYear = year - 1 if month == 1 else year
	nextMonth = 1 if month == 12 else month + 1
	nextYear = year + 1 if month == 12 else year
	row = []
	if bigAction.startswith("events:add"):
		row = [
			Button.inline("<<", create_calendar_callback_data(bigAction, "continue", prevYear, prevMonth)),
			Button.inline("Undo", bytes("%s" % ("events:add:startdate:start" if bigAction == "events:add:enddate:start" else "events:add:allday"), encoding='utf8')),
			Button.inline("Cancel", b'events'),
			Button.inline(">>", create_calendar_callback_data(bigAction, "continue", nextYear, nextMonth))
		]
	else:
		returnStr = ":".join(bigAction.split(":")[:3])
		row = [
			Button.inline("<<", create_calendar_callback_data(bigAction, "continue", prevYear, prevMonth)),
			Button.inline("Cancel", bytes(returnStr, encoding='utf8')),
			Button.inline(">>", create_calendar_callback_data(bigAction, "continue", nextYear, nextMonth))
		]
	keyboard.append(row)

	return keyboard

def create_clock_callback_data(bigAction, smallAction, hour, minute=None):
	if minute is None:
		return bytes(":".join([bigAction, smallAction, str(hour)]), encoding='utf8')
	else:
		return bytes(":".join([bigAction, smallAction, str(hour), str(minute)]), encoding='utf8')

def create_clock(bigAction, am, hour=None):
	keyboard = []

	if hour is None:
		# First row - AM or PM
		row = [
		   Button.inline("%s" % ("AM" if am else "PM"), create_clock_callback_data(bigAction, "continue", "%s" % ("pm" if am else "am"))) 
		]
		keyboard.append(row)

		# Rest of rows - Hours
		for hour1, hour2, hour3 in [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11)]:
			hour1Str = ("Midnight" if am else "Noon") if hour1 == 0 else ("%s AM" % (hour1) if am else "%s PM" % (hour1))
			hour2Str = "%s AM" % (hour2) if am else "%s PM" % (hour2)
			hour3Str = "%s AM" % (hour3) if am else "%s PM" % (hour3)
			row = [
				Button.inline(hour1Str, create_clock_callback_data(bigAction, "continue", hour1 + (0 if am else 12))),
				Button.inline(hour2Str, create_clock_callback_data(bigAction, "continue", hour2 + (0 if am else 12))),
				Button.inline(hour3Str, create_clock_callback_data(bigAction, "continue", hour3 + (0 if am else 12)))
			]
			keyboard.append(row)
		
	else:
		# First row - Go back
		row = [
		   Button.inline("<< Back to hour choice", create_clock_callback_data(bigAction, "continue", "%s" % ("am" if am else "pm"))) 
		]
		keyboard.append(row)

		realHour = hour if am else hour + 12

		# Rest of rows - Exact time
		for minute1, minute2, minute3 in [("00", "05", "10"), ("15", "20", "25"), ("30", "35", "40"), ("45", "50", "55")]:
			minute1Str = ("Midnight" if am else "Noon") if (hour == 0 and minute == "00") else ("%s:%s AM" % (hour, minute1) if am else "%s:%s PM" % (hour, minute1))
			minute2Str = ("%s:%s AM" % (hour, minute2) if am else "%s:%s PM" % (hour, minute2))
			minute3Str = ("%s:%s AM" % (hour, minute3) if am else "%s:%s PM" % (hour, minute3))
			row = [
				Button.inline(minute1Str, create_clock_callback_data(bigAction, "select", realHour, minute1)),
				Button.inline(minute2Str, create_clock_callback_data(bigAction, "select", realHour, minute2)),
				Button.inline(minute3Str, create_clock_callback_data(bigAction, "select", realHour, minute3))
			]
			keyboard.append(row)

	# Last row - Button
	row = []
	if bigAction.startswith("events:add"):
		row = [
			Button.inline("Undo", bytes("%s" % ("events:add:startdate:start" if bigAction == "events:add:enddate:start" else "events:add:allday"), encoding='utf8')),
			Button.inline("Cancel", b'events')
		]
	else:
		returnStr = ":".join(bigAction.split(":")[:3])
		row = [
			Button.inline("Cancel", bytes(returnStr, encoding='utf8')),
		]
	keyboard.append(row)

	return keyboard

async def show_events(event, prodFlag, cur, callback=False):
	events = retrieve_all_events_from_db(prodFlag, cur)
	text = ""
	if len(events) == 0:
		text = "Sorry, there are currently no upcoming IlliniFurs events. Please check again later!"
	else:
		textBuilder = "Here's a list of upcoming IlliniFurs events!"
		for (name, location, start, end, allDay, description) in events:
			when = getWhen(start, end, allDay)
			currText = """

**%s**
__Where:__ %s
__When:__ %s
__What:__ %s""" % (name, location, when, description)
			textBuilder = textBuilder + currText
		text = textBuilder
	buttons = None

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_top_level(event, who, conversationState, conversationData, IlliniFursState, callback=False):
	if who in conversationState:
		del conversationState[who]
	if who in conversationData:
		del conversationData[who]

	text = "What would you like to do with the event settings?"   
	buttons = [
		[
			Button.inline("Add a new event.", b'events:add:name'),
			Button.inline("Remove an event.", b'events:remove')
		], [
			Button.inline("Edit an event.", b'events:edit'),
			Button.inline("Edit the weekly meeting.", b'events:weekly')
		], [
			Button.inline("Announce a meeting.", b'events:announce'),
			Button.inline("<< Back to admin menu.", b'admin')
		]
	]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_name_prompt(event, who, conversationState, conversationData, IlliniFursState, callback=False, edit=None):
	text = "Ok, tell me the name of the event."
	buttons = []
	if edit is None:
		conversationState[who] = IlliniFursState.EVENT_ADD_NAME
		buttons = [
			Button.inline("Cancel", b'events')
		]
	elif isinstance(edit, str):
		conversationState[who] = IlliniFursState.EVENT_WEEKLY_NAME
		buttons = [
			Button.inline("Cancel", b'events:weekly')
		]
	else:
		conversationState[who] = IlliniFursState.EVENT_EDIT_NAME
		buttons = [
			Button.inline("Cancel", bytes("events:edit:%s:gen" % (str(edit)), encoding='utf8'))
		]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_location_prompt(event, who, conversationState, conversationData, IlliniFursState, callback=False, edit=None):
	text = "Where will this event take place?"
	buttons = []
	if edit is None:
		conversationState[who] = IlliniFursState.EVENT_ADD_LOCATION
		buttons = [
			Button.inline("Undo", b'events:add:name'),
			Button.inline("Cancel", b'events')
		]
	elif isinstance(edit, str):
		conversationState[who] = IlliniFursState.EVENT_WEEKLY_LOCATION
		buttons = [
			Button.inline("Cancel", b'events:weekly')
		]
	else:
		conversationState[who] = IlliniFursState.EVENT_EDIT_LOCATION
		buttons = [
			Button.inline("Cancel", bytes("events:edit:%s:gen" % (str(edit)), encoding='utf8'))
		]
	
	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_allday_prompt(event, who, conversationState, conversationData, IlliniFursState, callback=False, edit=None):
	if who in conversationState:
		del conversationState[who]

	text = "Will this event be an all-day event?"
	buttons = []
	if edit is None:
		buttons = [
			[
				Button.inline("Yes", b'events:add:allday:yes'),
				Button.inline("No", b'events:add:allday:no')
			], [
				Button.inline("Undo", b'events:add:location'),
				Button.inline("Cancel", b'events')
			]
		]
	else:
		buttons = [
			[
				Button.inline("Yes", bytes("events:edit:%s:allday:yes" % str(edit), encoding='utf8')),
				Button.inline("No", bytes("events:edit:%s:allday:no" % str(edit), encoding='utf8'))
			], [
				Button.inline("Cancel", bytes("events:edit:%s:gen" % str(edit), encoding='utf8'))
			]
		]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_weekly_day_prompt(event):
	text = "What day of the week will the weekly meeting be?"
	buttons = [
		[
			Button.inline("Sunday", b'events:weekly:day:1'),
			Button.inline("Monday", b'events:weekly:day:2')
		], [
			Button.inline("Tuesday", b'events:weekly:day:3'),
			Button.inline("Wednesday", b'events:weekly:day:4')
		], [
			Button.inline("Thursday", b'events:weekly:day:5'),
			Button.inline("Friday", b'events:weekly:day:6')
		], [
			Button.inline("Saturday", b'events:weekly:day:7'),
			Button.inline("Cancel", b'events:weekly')
		]
	]

	await event.edit(text, buttons=buttons)

async def events_date_prompt(event, start, bigAction, year=None, month=None):
	text = "What day will your event %s? (Be sure to use Central time)" % ("start" if start else "end")
	buttons = create_calendar(bigAction, year, month)

	await event.edit(text, buttons=buttons)

async def events_time_prompt(event, start, bigAction, am=True, hour=None):
	text = "What time will your event %s? (Be sure to use Central time)" % ("start" if start else "end")
	buttons = create_clock(bigAction, am, hour)

	await event.edit(text, buttons=buttons)

async def events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, callback=False, edit=None):
	text = "Describe the event. Note: if you use Markdown notation, that will render on the website!"
	buttons = []
	if edit is None:
		conversationState[who] = IlliniFursState.EVENT_ADD_DESCRIPTION
		buttons = [
			Button.inline("Undo", b'events:add:enddate'),
			Button.inline("Cancel", b'events')
		]
	elif isinstance(edit, str):
		conversationState[who] = IlliniFursState.EVENT_WEEKLY_DESCRIPTION
		buttons = [
			Button.inline("Cancel", b'events:weekly')
		]
	else:
		conversationState[who] = IlliniFursState.EVENT_EDIT_DESCRIPTION
		buttons = [
			Button.inline("Cancel", bytes("events:edit:%s:gen" % (str(edit)), encoding='utf8'))
		]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def events_add_final_prompt(event, who, conversationState, conversationData, IlliniFursState, callback=False): 
	name = conversationData[who]["name"]
	location = conversationData[who]["location"]
	allDay = "Yes" if conversationData[who]["allDay"] else "No"
	start = conversationData[who]["start"].strftime("%A, %B %-d, %Y %-I:%M %p")
	end = conversationData[who]["end"].strftime("%A, %B %-d, %Y %-I:%M %p")
	description = conversationData[who]["description"]
	text = """Here's the information you added. Accept this event?

Name: %s
Location: %s
Start: %s
End: %s
All-day: %s
Description: %s""" % (name, location, start, end, allDay, description)
	
	buttons = [
		[
			Button.inline("Accept Event", b'events:add:final')
		], [
			Button.inline("Change Name", b'events:add:name'),
			Button.inline("Change Location", b'events:add:location')
		], [
			Button.inline("Change Start", b'events:add:startdate'),
			Button.inline("Change End", b'events:add:enddate')
		], [
			Button.inline("Change All-day", b'events:add:allday'),            
			Button.inline("Change Description", b'events:add:description')
		], [
			Button.inline("Cancel", b'events')
		]
	]

	if callback:
		await event.edit(text, buttons=buttons)
	else:
		await event.respond(text, buttons=buttons)

async def init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, adminTest):
	@bot.on(events.NewMessage(pattern='/events'))
	async def handler(event):
		await show_events(event, prodFlag, cur)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:show'))
	async def handler(event):
		await show_events(event, prodFlag, cur, True)
		raise events.StopPropagation

	@bot.on(events.NewMessage(pattern='/eventMenu'))
	async def handler(event):
		if await adminTest(event, cur):
			sender = await event.get_sender()
			who = sender.id
			await events_top_level(event, who, conversationState, conversationData, IlliniFursState)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			await events_top_level(event, who, conversationState, conversationData, IlliniFursState, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:add:name'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			await events_name_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
			
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:add:location'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			await events_location_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:add:allday'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			await events_allday_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:allday:(yes|no)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			allDay = (event.data_match[1].decode('utf8') == "yes")
			conversationData[who].update({"allDay": allDay})

			await events_date_prompt(event, True, "events:add:startdate")
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)date')))
	async def handler(event):
		if await adminTest(event, cur, True):
			start = (event.data_match[1].decode('utf8') == "start")

			await events_date_prompt(event, start, "events:add:%sdate" % ("start" if start else "end"))
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)date:continue:([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			start = (event.data_match[1].decode('utf8') == "start")
			year = int(event.data_match[2].decode('utf8'))
			month = int(event.data_match[3].decode('utf8'))

			await events_date_prompt(event, start, "events:add:%sdate" % ("start" if start else "end"), year, month)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)date:select:([0-9]*):([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			start = (event.data_match[1].decode('utf8') == "start")
			year = int(event.data_match[2].decode('utf8'))
			month = int(event.data_match[3].decode('utf8'))
			day = int(event.data_match[4].decode('utf8'))
			hour = 0 if start else 23
			minute = 0 if start else 59
			conversationData[who].update({("%s" % ("start" if start else "end")): datetime.datetime(year, month, day, hour, minute)})

			if start:
				if conversationData[who]["allDay"]:
					await events_date_prompt(event, False, "events:add:enddate")
				else:
					await events_time_prompt(event, True, "events:add:starttime")
			else:
				if conversationData[who]["allDay"]:
					await events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
				else:
					await events_time_prompt(event, False, "events:add:endtime")
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)time:continue:(am|pm)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			start = (event.data_match[1].decode('utf8') == "start")
			am = (event.data_match[2].decode('utf8') == "am")

			await events_time_prompt(event, start, "events:add:%stime" % ("start" if start else "end"), am)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)time:continue:([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			start = (event.data_match[1].decode('utf8') == "start")
			hour = int(event.data_match[2].decode('utf8'))
			am = True
			if hour >= 12:
				hour = hour - 12
				am = False

			await events_time_prompt(event, start, "events:add:%stime" % ("start" if start else "end"), am, hour)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:add:(start|end)time:select:([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			start = (event.data_match[1].decode('utf8') == "start")
			hour = int(event.data_match[2].decode('utf8'))
			minute = int(event.data_match[3].decode('utf8'))
			realDate = conversationData[who]["%s" % ("start" if start else "end")].replace(hour=hour, minute=minute)
			conversationData[who]["%s" % ("start" if start else "end")] = realDate

			if start:
				await events_date_prompt(event, False, "events:add:enddate")
			else:
				await events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:add:description'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			await events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, True)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:add:final'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id

			name = conversationData[who]["name"]
			location = conversationData[who]["location"]
			start = conversationData[who]["start"].strftime("%Y-%m-%d %H:%M:%S")
			end = conversationData[who]["end"].strftime("%Y-%m-%d %H:%M:%S")
			allDay = conversationData[who]["allDay"]
			description = conversationData[who]["description"]

			add_event_to_db(prodFlag, con, cur, name, location, start, end, allDay, description)
			text = "Event added to database!"
			buttons = [
				[Button.inline("Add another event", b'events:add:name')],
				[Button.inline("<< Back to event menu", b'events')]
			]

			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:remove'))
	async def handler(event):
		if await adminTest(event, cur, True):
			text = "Which event would you like to remove?"
			events = retrieve_event_from_db(prodFlag, cur)
			buttons = [ [Button.inline(name, bytes("events:remove:%s" % str(eventId), encoding="utf8"))] for eventId, name, start in events ]
			buttons.append([Button.inline("<< Back to events menu", b'events')])
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:remove:([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = int(event.data_match[1].decode('utf8'))
			remove_event_from_db(prodFlag, con, cur, eventId)
			text = "Event removed from DB! Would you like to remove another?"
			buttons = [
				Button.inline("Remove another event", b'events:remove'),
				Button.inline("<< Back to events menu", b'events')
			]
			
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:edit'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			text = "Which event would you like to edit?"
			events = retrieve_event_from_db(prodFlag, cur)
			buttons = [ [Button.inline(name, bytes("events:edit:%s:gen" % str(eventId), encoding="utf8"))] for eventId, name, start in events]
			buttons.append([Button.inline("<< Back to events menu", b'events')])
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):gen')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]

			eventId = int(event.data_match[1].decode('utf8'))
			(name, location, start, end, allDay, description) = retrieve_event_from_db(prodFlag, cur, eventId)
			start = start.strftime("%A, %B %-d, %Y %-I:%M %p")
			end = end.strftime("%A, %B %-d, %Y %-I:%M %p")
			text = """Editing info for event.

Name: %s
Location: %s
Start: %s
End: %s
All-day: %s
Description: %s""" % (name, location, start, end, "Yes" if allDay else "No", description)
			buttons = [
				[
					Button.inline("Change Name", bytes("events:edit:%s:name" % str(eventId), encoding='utf8')),
					Button.inline("Change Location", bytes("events:edit:%s:location" % str(eventId), encoding='utf8'))
				], [
					Button.inline("Change Start", bytes("events:edit:%s:startdate:start" % str(eventId), encoding='utf8')),
					Button.inline("Change End", bytes("events:edit:%s:enddate:start" % str(eventId), encoding='utf8'))
				], [
					Button.inline("Change All-day", bytes("events:edit:%s:allday" % str(eventId), encoding='utf8')),            
					Button.inline("Change Description", bytes("events:edit:%s:description" % str(eventId), encoding='utf8'))
				], [
					Button.inline("<< Back to event list", b'events:edit')
				]
			]
			conversationData[who] = {"allDay": allDay}
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):name')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			conversationData[who] = {"eventId": eventId}
			await events_name_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):location')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			conversationData[who] = {"eventId": eventId}
			await events_location_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):allday')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			await events_allday_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):allday:(yes|no)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			allDay = (event.data_match[2].decode('utf8') == "yes")
			update_event_in_db(prodFlag, con, cur, eventId, allDay=allDay)
			text = "All-day status of event changed!"
			buttons = [
				Button.inline("Continue editing", bytes("events:edit:%s:gen" % str(eventId), encoding="utf8")),
				Button.inline("<< Back to event list", b'events:edit')
			]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)date:start')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = int(event.data_match[1].decode('utf8'))
			start = event.data_match[2].decode('utf8') == "start"
			await events_date_prompt(event, start, "events:edit:%s:%sdate" % (str(eventId), "start" if start else "end"))
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)date:continue:([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = int(event.data_match[1].decode('utf8'))
			start = (event.data_match[2].decode('utf8') == "start")
			year = int(event.data_match[3].decode('utf8'))
			month = int(event.data_match[4].decode('utf8'))
			await events_date_prompt(event, start, "events:edit:%s:%sdate" % (str(eventId), "start" if start else "end"), year, month)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)date:select:([0-9]*):([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			start = (event.data_match[2].decode('utf8') == "start")
			year = int(event.data_match[3].decode('utf8'))
			month = int(event.data_match[4].decode('utf8'))
			day = int(event.data_match[5].decode('utf8'))
			hour = 0 if start else 23
			minute = 0 if start else 59

			if conversationData[who]["allDay"]:
				timeStr = datetime.datetime(year, month, day, hour, minute).strftime("%Y-%m-%d %H:%M:%S")
				text = ""
				if start:
					update_event_in_db(prodFlag, con, cur, eventId, start=timeStr)
					text = "Start of event changed!"
				else:
					update_event_in_db(prodFlag, con, cur, eventId, end=timeStr)
					text = "End of event changed!"
					
				buttons = [
					Button.inline("Continue editing", bytes("events:edit:%s:gen" % str(eventId), encoding="utf8")),
					Button.inline("<< Back to event list", b'events:edit')
				]

				await event.edit(text, buttons=buttons)
			else:
				conversationData[who].update({"datetime": datetime.datetime(year, month, day, hour, minute)})
				await events_time_prompt(event, start, "events:edit:%s:%stime" % (str(eventId), "start" if start else "end"))
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)time:continue:(am|pm)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = int(event.data_match[1].decode('utf8'))
			start = (event.data_match[2].decode('utf8') == "start")
			am = (event.data_match[3].decode('utf8') == "am")

			await events_time_prompt(event, start, "events:edit:%s:%stime" % (str(eventId), "start" if start else "end"), am)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)time:continue:([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = int(event.data_match[1].decode('utf8'))
			start = (event.data_match[2].decode('utf8') == "start")
			hour = int(event.data_match[3].decode('utf8'))
			am = True
			if hour >= 12:
				hour = hour - 12
				am = False

			await events_time_prompt(event, start, "events:edit:%s:%stime" % (str(eventId), "start" if start else "end"), am, hour)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):(start|end)time:select:([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			start = (event.data_match[2].decode('utf8') == "start")
			hour = int(event.data_match[3].decode('utf8'))
			minute = int(event.data_match[4].decode('utf8'))
			realDate = conversationData[who]["datetime"].replace(hour=hour, minute=minute)

			timeStr = realDate.strftime("%Y-%m-%d %H:%M:%S")
			text = ""
			if start:
				update_event_in_db(prodFlag, con, cur, eventId, start=timeStr)
				text = "Start of event changed!"
			else:
				update_event_in_db(prodFlag, con, cur, eventId, end=timeStr)
				text = "End of event changed!"

			buttons = [
				Button.inline("Continue editing", bytes("events:edit:%s:gen" % str(eventId), encoding="utf8")),
				Button.inline("<< Back to event list", b'events:edit')
			]

			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:edit:([0-9]*):description')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = int(event.data_match[1].decode('utf8'))
			conversationData[who] = {"eventId": eventId}
			await events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:weekly'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			(name, location, startTime, endTime, dayOfWeek, description) = retrieve_weekly_from_db(prodFlag, cur)
			startTime = startTime.strftime("%-I:%M %p")
			endTime = endTime.strftime("%-I:%M %p")
			dayOfWeek = calendar.day_name[(dayOfWeek + 5) % 7]
			text = """Here is the current information set for the weekly meetings.

Name: %s
Location: %s
Start Time: %s
End Time: %s
Day of Week: %s
Description: %s""" % (name, location, startTime, endTime, dayOfWeek, description)
			buttons = [
				[
					Button.inline("Change Name", b'events:weekly:name'),
					Button.inline("Change Location", b'events:weekly:location')
				], [
					Button.inline("Change Start", b'events:weekly:starttime:continue:am'),
					Button.inline("Change End", b'events:weekly:endtime:continue:am')
				], [
					Button.inline("Change Day of Week", b'events:weekly:day'),            
					Button.inline("Change Description", b'events:weekly:description')
				], [
					Button.inline("<< Back to event menu", b'events')
				]
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:weekly:name'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = 'weekly'
			await events_name_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:weekly:location'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = 'weekly'
			await events_location_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:weekly:day'))
	async def handler(event):
		if await adminTest(event, cur, True):
			await events_weekly_day_prompt(event)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:weekly:day:([1-7])')))
	async def handler(event):
		if await adminTest(event, cur, True):
			dayOfWeek = int(event.data_match[1].decode('utf8'))
			update_weekly_in_db(prodFlag, con, cur, dayOfWeek=dayOfWeek)
			text = "Day of weekly event changed!"

			buttons = [
				Button.inline("Continue editing", b'events:weekly'),
				Button.inline("<< Back to event menu", b'events')
			]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:weekly:(start|end)time:continue:(am|pm)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = 'weekly'
			start = (event.data_match[1].decode('utf8') == "start")
			am = (event.data_match[2].decode('utf8') == "am")

			await events_time_prompt(event, start, "events:weekly:%stime" % "start" if start else "end", am)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:weekly:(start|end)time:continue:([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			eventId = 'weekly'
			start = (event.data_match[1].decode('utf8') == "start")
			hour = int(event.data_match[2].decode('utf8'))
			am = True
			if hour >= 12:
				hour = hour - 12
				am = False

			await events_time_prompt(event, start, "events:weekly:%stime" % "start" if start else "end", am, hour)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:weekly:(start|end)time:select:([0-9]*):([0-9]*)')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			start = (event.data_match[1].decode('utf8') == "start")
			hour = int(event.data_match[2].decode('utf8'))
			minute = int(event.data_match[3].decode('utf8'))
			realDate = datetime.time(hour, minute)

			timeStr = realDate.strftime("%H:%M:%S")
			text = ""
			if start:
				update_weekly_in_db(prodFlag, con, cur, startTime=timeStr)
				text = "Start of weekly event changed!"
			else:
				update_weekly_in_db(prodFlag, con, cur, endTime=timeStr)
				text = "End of weekly event changed!"

			buttons = [
				Button.inline("Continue editing", b'events:weekly'),
				Button.inline("<< Back to event menu", b'events')
			]

			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:weekly:description'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			eventId = 'weekly'
			await events_description_prompt(event, who, conversationState, conversationData, IlliniFursState, True, eventId)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=b'events:announce'))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]
			if who in conversationData:
				del conversationData[who]

			text = "Which event would you like to announce?"
			events = retrieve_event_from_db(prodFlag, cur)
			buttons = [ [Button.inline(name, bytes("events:announce:%s:confirm" % str(eventId), encoding="utf8"))] for eventId, name, start in events]
			buttons.append([Button.inline("<< Back to events menu", b'events')])
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:announce:([0-9]*):confirm')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]

			eventId = int(event.data_match[1].decode('utf8'))
			(name, location, start, end, allDay, description) = retrieve_event_from_db(prodFlag, cur, eventId)
			when = getWhen(start, end, allDay)
			text = """Here's what the announcement will look like. Are you sure?

**%s**
__Where:__ %s
__When:__ %s

%s""" % (name, location, when, description)
			buttons = [
				[
					Button.inline("Announce the event.", bytes("events:announce:%s:go" % str(eventId), encoding='utf8')),
					Button.inline("Edit the event.", bytes("events:edit:%s:gen" % str(eventId), encoding='utf8'))
				], [
					Button.inline("<< Back to event list", b'events:announce')
				]
			]
			await event.edit(text, buttons=buttons)
		raise events.StopPropagation

	@bot.on(events.CallbackQuery(data=re.compile(b'events:announce:([0-9]*):go')))
	async def handler(event):
		if await adminTest(event, cur, True):
			sender = await event.get_sender()
			who = sender.id
			if who in conversationState:
				del conversationState[who]

			eventId = int(event.data_match[1].decode('utf8'))
			(name, location, start, end, allDay, description) = retrieve_event_from_db(prodFlag, cur, eventId)
			when = getWhen(start, end, allDay)
			announceText = """**%s**
__Where:__ %s
__When:__ %s

%s""" % (name, location, when, description)

			announceChannelId = retrieve_announce_channel_from_db(prodFlag, cur)
			announceChannelId = int("-100%d" % announceChannelId)
			announceChannel = await bot.get_entity(announceChannelId)
			await bot.send_message(announceChannel, announceText)

			text = "%s announced!" % name
			buttons = [
				Button.inline("<< Back to event list", b'events:announce')
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

		if state == IlliniFursState.EVENT_ADD_NAME:
			if await adminTest(event, cur):
				sender = await event.get_sender()
				who = sender.id
				conversationData[who] = {"name": event.text}
				
				await events_location_prompt(event, who, conversationState, conversationData, IlliniFursState)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		if state == IlliniFursState.EVENT_ADD_LOCATION:
			if await adminTest(event, cur):
				sender = await event.get_sender()
				who = sender.id
				if "location" in conversationData[who]:
					conversationData[who]["location"] = event.text
				else:    
					conversationData[who].update({"location": event.text})
				
				await events_allday_prompt(event, who, conversationState, conversationData, IlliniFursState)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		if state == IlliniFursState.EVENT_ADD_DESCRIPTION:
			if await adminTest(event, cur):
				sender = await event.get_sender()
				who = sender.id
				if "description" in conversationData[who]:
					conversationData[who]["description"] = event.text
				else:    
					conversationData[who].update({"description": event.text})
				
				await events_add_final_prompt(event, who, conversationState, conversationData, IlliniFursState)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		if (state == IlliniFursState.EVENT_EDIT_NAME or state == IlliniFursState.EVENT_EDIT_LOCATION or state == IlliniFursState.EVENT_EDIT_DESCRIPTION):
			if await adminTest(event, cur):
				sender = await event.get_sender()
				who = sender.id
				eventId = conversationData[who]["eventId"]
				
				text = ""
				if state == IlliniFursState.EVENT_EDIT_NAME:
					update_event_in_db(prodFlag, con, cur, eventId, name=event.text)
					text = "Name of event changed!"
				if state == IlliniFursState.EVENT_EDIT_LOCATION:
					update_event_in_db(prodFlag, con, cur, eventId, location=event.text)
					text = "Location of event changed!"
				if state == IlliniFursState.EVENT_EDIT_DESCRIPTION:
					update_event_in_db(prodFlag, con, cur, eventId, description=event.text)
					text = "Description of event changed!"

				buttons = [
					Button.inline("Continue editing", bytes("events:edit:%s:gen" % str(eventId), encoding="utf8")),
					Button.inline("<< Back to event list", b'events:edit')
				]

				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]

				await event.respond(text, buttons=buttons)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation

		if (state == IlliniFursState.EVENT_WEEKLY_NAME or state == IlliniFursState.EVENT_WEEKLY_LOCATION or state == IlliniFursState.EVENT_WEEKLY_DESCRIPTION):
			if await adminTest(event, cur):
				sender = await event.get_sender()
				who = sender.id
				
				text = ""
				if state == IlliniFursState.EVENT_WEEKLY_NAME:
					update_weekly_in_db(prodFlag, con, cur, name=event.text)
					text = "Name of weekly meeting changed!"
				if state == IlliniFursState.EVENT_WEEKLY_LOCATION:
					update_weekly_in_db(prodFlag, con, cur, location=event.text)
					text = "Location of weekly meeting changed!"
				if state == IlliniFursState.EVENT_WEEKLY_DESCRIPTION:
					update_weekly_in_db(prodFlag, con, cur, description=event.text)
					text = "Description of weekly meeting changed!"

				buttons = [
					Button.inline("Continue editing", b'events:weekly'),
					Button.inline("<< Back to event menu", b'events')
				]

				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]

				await event.respond(text, buttons=buttons)
			else:
				if who in conversationState:
					del conversationState[who]
				if who in conversationData:
					del conversationData[who]
			raise events.StopPropagation
