import sqlite3

conn = sqlite3.connect('my_blogs.db')

conn.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        short_description TEXT NOT NULL,
        description TEXT NOT NULL,
        post_part1 TEXT NOT NULL,
        post_part2 TEXT,
        author TEXT NOT NULL,
        imageURL TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS announcemet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        post_part1 TEXT NOT NULL,
        imageURL TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS announcement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        post_part1 TEXT NOT NULL,
        imageURL TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        question TEXT NOT NULL
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("Database and tables created successfully.")
