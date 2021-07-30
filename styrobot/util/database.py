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
