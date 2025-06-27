import sqlite3

conn = sqlite3.connect('my_blogs.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS announcemet")



conn.commit()
conn.close()
