import sqlite3

db_path = 'database.db'

def create_connection(db_file = db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


conn = create_connection()

cur = conn.cursor()

sql = '''
CREATE TABLE IF NOT EXISTS users (
    userID INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)
'''
cur.execute(sql)

sql = '''
CREATE TABLE IF NOT EXISTS movies (
    imdbID TEXT PRIMARY KEY
)
'''
cur.execute(sql)

sql = '''
CREATE TABLE IF NOT EXISTS tags (
    tagID INTEGER PRIMARY KEY,
    tag_name TEXT
)
'''
cur.execute(sql)

sql = '''
CREATE TABLE IF NOT EXISTS scored_tags (
    sctagID INTEGER PRIMARY KEY,
    movie_id TEXT REFERENCES movies(imdbID),
    tag_id INTEGER REFERENCES tags(tagID),
    score INTEGER
)
'''
cur.execute(sql)
cur.execute('INSERT INTO tags (tag_name) VALUES ("Movie")')

conn.commit()
