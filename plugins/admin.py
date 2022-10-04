def adminTest(event, cur):
    cur.execute("SELECT id FROM officers")
    admins = {adminId for (adminId,) in cur.fetchall()}
    return event.sender_id in admins
