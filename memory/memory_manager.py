import sqlite3
import os
import time

DB = os.path.join(os.path.dirname(__file__), 'memory_db.sqlite')

def _conn():
    first = not os.path.exists(DB)
    c = sqlite3.connect(DB)
    if first:
        cur = c.cursor()
        cur.execute('CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT, last_updated INTEGER)')
        cur.execute('CREATE TABLE embeddings (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, vector BLOB, created INTEGER)')
        c.commit()
    return c

def save_memory(key, value):
    c = _conn(); cur = c.cursor()
    cur.execute('REPLACE INTO kv (key,value,last_updated) VALUES (?,?,?)', (key, value, int(time.time())))
    c.commit(); c.close()

def query_memory(key):
    c = _conn(); cur = c.cursor()
    cur.execute('SELECT value FROM kv WHERE key=?', (key,))
    row = cur.fetchone()
    c.close()
    return row[0] if row else None

# Semantic search stub (to be implemented with embeddings)
def semantic_search(query, top_k=5):
    return []
