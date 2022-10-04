from telethon import events

SITE_SCRIPT = os.path.expanduser("~/site/source/post_deploy.sh")
BOT_SCRIPT = os.path.expanduser("~/bot/post_deploy.sh")

def adminTest(event, cur):
    cur.execute("SELECT id FROM officers")
    admins = {adminId for (adminId,) in cur.fetchall()}
    return event.sender_id in admins

async def init(bot, cur, adminTest):
    @bot.on(events.NewMessage(pattern='/reloadSite'))
    async def handler(event):
        if adminTest(event, cur):
            event.reply("Reloading site!")
            os.system('bash ' + SITE_SCRIPT)

    @bot.on(events.NewMessage(pattern='/reloadBot'))
    async def handler(event):
        if adminTest(event, cur):
            event.reply("Reloading bot!")
            os.system('bash ' + BOT_SCRIPT)
