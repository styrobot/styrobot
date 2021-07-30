import sqlite3
import os

persist_root = '/tmp/persist/'
db_root = os.path.join(persist_root, 'sqlite')

if not os.path.isdir(db_root):
    os.mkdir(db_root)

def open_common_database():
    con = sqlite3.connect(os.path.join(db_root, 'common.sqlite3'))
    return con

def open_guild_database(guild_id):
    assert isinstance(guild_id, int)
    con = sqlite3.connect(os.path.join(db_root, f'{guild_id}.sqlite3'))
    return con

def create_guild_settings_table(con):
    con.execute('''CREATE TABLE IF NOT EXISTS settings (key text NOT NULL UNIQUE PRIMARY KEY, value text)''')
    con.commit()

def get_guild_setting(guild_id, setting_name, default=None, con=None):
    """
    Most cogs will only need to read guild settings, not write them.
    """
    close = (con is None)
    if con is None:
        con = open_guild_database(guild_id)
    create_guild_settings_table(con)
    cur = con.cursor()
    cur.execute('SELECT value FROM settings WHERE key=?', (setting_name,))
    res = cur.fetchone()
    if res is not None:
        res = res[0]
    else:
        res = default
    if close:
        con.close()
    return res