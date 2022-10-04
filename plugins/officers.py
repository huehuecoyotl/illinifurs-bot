import re
import os
from enum import Enum, auto
from telethon import Button, utils, events

OFFICERS_DIRECTORY = os.path.expanduser("~/site/source/public/images/officers/")

def retrieve_officer_from_db(prodFlag, cur, title):
    query = ""
    if prodFlag:
        query = "SELECT * FROM officers WHERE title=%s"
    else:
        query = "SELECT * FROM officers WHERE title=?"
    cur.execute(query, (title,))
    retval = cur.fetchall()
    if len(retval) == 0:
        return None
    return retval[0]

def add_officer_to_db(prodFlag, con, cur, adminId, username, title, imageURL):
    chatInviter = False
    if title == "President" or title == "Vice President":
        chatInviter = True
    query = ""
    queryVars = (adminId, username, title, imageURL, chatInviter)
    if prodFlag:
        query1 = "DELETE FROM officers WHERE title=%s"
        query2 = "INSERT INTO officers (id, username, title, imageURL, chatInviter) VALUES (%s, %s, %s, %s, %s)"
    else:
        query1 = "DELETE FROM officers WHERE title=?"
        query2 = "INSERT INTO officers (id, username, title, imageURL, chatInviter) VALUES (?, ?, ?, ?, ?)"
    cur.execute(query1, (title,))
    cur.execute(query2, queryVars)
    con.commit()

def update_officer_image_in_db(prodFlag, con, cur, adminId, imageURL):
    query = ""
    queryVars = (imageURL, adminId)
    if prodFlag:
        query = "UPDATE officers SET imageURL=%s WHERE id=%s"
    else:
        query = "UPDATE officers SET imageURL=? WHERE id=?"
    cur.execute(query, queryVars)
    con.commit()

async def download_profile_pic(bot, prodFlag, user, baseTitle):
    allPhotos = await bot.get_profile_photos(user)
    photo = allPhotos[0]
    filename = await bot.download_media(photo)
    extension = utils.get_extension(photo)
    if prodFlag:
        os.system("mv %s %s%s%s" % (filename, OFFICERS_DIRECTORY, baseTitle, extension))
    else:
        os.system("mv %s %s%s" % (filename, baseTitle, extension))
    return "/images/officers/%s%s" % (baseTitle, extension)

async def officers_top_level(event, conversationState, conversationData, callback=False):
    sender = await event.get_sender()
    who = sender.id
    if who in conversationState:
        del conversationState[who]
    if who in conversationData:
        del conversationData[who]

    text = "Which IlliniFurs officer would you like to edit?"
    buttons = [
        Button.inline("President", b'officers:president'),
        Button.inline("Treasurer", b'officers:treasurer'),
        Button.inline("VP", b'officers:vp')
    ]

    if callback:
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

async def init(bot, prodFlag, con, cur, conversationState, conversationData, IlliniFursState, adminTest):
    @bot.on(events.NewMessage(pattern='/officers'))
    async def handler(event):
        if await adminTest(event, cur):
            await officers_top_level(event, conversationState, conversationData)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=b'officers'))
    async def handler(event):
        if await adminTest(event, cur):
            await officers_top_level(event, conversationState, conversationData, True)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=re.compile(b'officers:(president|treasurer|vp)')))
    async def handler(event):
        if await adminTest(event, cur):
            sender = await event.get_sender()
            who = sender.id
            if who in conversationState:
                del conversationState[who]
            if who in conversationData:
                del conversationData[who]
            baseTitle = event.data_match[1].decode('utf8')
            title = ""
            if baseTitle == "president":
                title = "President"
            elif baseTitle == "treasurer":
                title = "Treasurer"
            elif baseTitle == "vp":
                title = "Vice President"
            response = retrieve_officer_from_db(prodFlag, cur, title)
            username = None
            imageURL = None
            if response is not None:
                (adminId, username, title, imageURL, chatInviter) = response
            if imageURL is not None and not imageURL.startswith("http"):
                imageURL = "https://illinifurs.com%s" % imageURL
            text = """Editing %s's info.

Username: @%s
Profile Pic: %s""" % (title, username, imageURL)
            buttons = [
                [
                    Button.inline("Update to new user", bytes("officers:%s:user" % baseTitle, encoding="utf8")),
                    Button.inline("Refresh profile pic", bytes("officers:%s:pic" % baseTitle, encoding="utf8"))
                ],
                [Button.inline("<< Back to officers menu", b'officers')]
            ]
            await event.edit(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=re.compile(b'officers:(president|treasurer|vp):user')))
    async def handler(event):
        if await adminTest(event, cur):
            sender = await event.get_sender()
            who = sender.id
            baseTitle = event.data_match[1].decode('utf8')
            title = ""
            if baseTitle == "president":
                title = "President"
            elif baseTitle == "treasurer":
                title = "Treasurer"
            elif baseTitle == "vp":
                title = "Vice President"
            conversationState[who] = IlliniFursState.OFFICER_ADD
            conversationData[who] = {"baseTitle": baseTitle}
            text = "Please enter the username of the new %s. (Be sure to include the '@'.)" % title
            buttons = [Button.inline("Cancel", bytes("officers:%s" % baseTitle, encoding="utf8"))]
            await event.edit(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=re.compile(b'officers:(president|treasurer|vp):pic')))
    async def handler(event):
        if await adminTest(event, cur):
            baseTitle = event.data_match[1].decode('utf8')
            title = ""
            if baseTitle == "president":
                title = "President"
            elif baseTitle == "treasurer":
                title = "Treasurer"
            elif baseTitle == "vp":
                title = "Vice President"
            response = retrieve_officer_from_db(prodFlag, cur, url)
            adminId = None
            username = None
            imageURL = None
            text = ""
            if response is not None:
                (adminId, username, title, imageURL, chatInviter) = response
                newImageURL = await download_profile_pic(bot, prodFlag, username, baseTitle)
                update_officer_image_in_db(prodFlag, con, cur, adminId, newImageURL)
                text = "The %s's profile pic has been refreshed! It is now https://illinifurs.com%s" % (title, newImageURL)
            else:
                text = "There appears to be no current %s. Please enter one into the DB first!" % title
            buttons = [
                Button.inline("Continue editing" , bytes("officers:%s" % baseTitle, encoding="utf8")),
                Button.inline("<< Back to officers menu", b'officers')
            ]
            await event.edit(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.NewMessage)
    async def handler(event):
        if await adminTest(event, cur):
            sender = await event.get_sender()
            who = sender.id
            currState = conversationState.get(who)

            if currState is None:
                return

            elif currState == IlliniFursState.OFFICER_ADD:
                text = ""

                username = event.text
                if username[0] != '@':
                    text = "That didn't have an @ sign! Are you sure that's a username? (Please try again.)"
                    await event.respond(text)
                else:
                    username = username[1:]
                    data = conversationData.get(who)

                    baseTitle = data['baseTitle']
                    title = ""
                    if baseTitle == "president":
                        title = "President"
                    elif baseTitle == "treasurer":
                        title = "Treasurer"
                    elif baseTitle == "vp":
                        title = "Vice President"

                    if who in conversationState:
                        del conversationState[who]
                    if who in conversationData:
                        del conversationData[who]

                    user = await bot.get_entity(username)
                    adminId = user.id
                    imageURL = await download_profile_pic(bot, prodFlag, username, baseTitle)
                    add_officer_to_db(prodFlag, con, cur, adminId, username, title, imageURL)

                    text = "Success! The %s has been updated." % title
                    buttons = [
                        Button.inline("<< Back to officers menu", b'officers')
                    ]

                    await event.respond(text, buttons=buttons)
