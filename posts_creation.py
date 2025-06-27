import sqlite3

conn = sqlite3.connect('../my_blogs.db')
c = conn.cursor()

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

conn.close()