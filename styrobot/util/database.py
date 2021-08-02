import aiosqlite
import os

persist_root = '/tmp/persist/'
db_root = os.path.join(persist_root, 'sqlite')

if not os.path.isdir(db_root):
    os.mkdir(db_root)


async def open_common_database():
    con = await aiosqlite.connect(os.path.join(db_root, 'common.sqlite3'))
    return con


async def open_guild_database(guild_id):
    assert isinstance(guild_id, int)
    con = await aiosqlite.connect(os.path.join(db_root, f'{guild_id}.sqlite3'))
    return con


async def create_guild_settings_table(con):
    await con.execute('''CREATE TABLE IF NOT EXISTS settings (key text NOT NULL UNIQUE PRIMARY KEY, value text)''')
    await con.commit()


async def get_guild_setting(guild_id, setting_name, default=None, con=None):
    """
    Most cogs will only need to read guild settings, not write them.
    """
    close = (con is None)
    if con is None:
        con = await open_guild_database(guild_id)
    await create_guild_settings_table(con)
    cur = await con.execute('SELECT value FROM settings WHERE key=?', (setting_name,))
    res = await cur.fetchone()
    if res is not None:
        res = res[0]
    else:
        res = default
    if close:
        await con.close()
    return res
