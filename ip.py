import sqlite3

def add_columns_to_users_table(db_path='my_blogs.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Try to add ip_address column
        cursor.execute("ALTER TABLE users ADD COLUMN ip_address TEXT")
        print("Added 'ip_address' column.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("'ip_address' column already exists.")
        else:
            raise

    try:
        # Try to add user_agent column
        cursor.execute("ALTER TABLE users ADD COLUMN user_agent TEXT")
        print("Added 'user_agent' column.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("'user_agent' column already exists..")
        else:
            raise

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns_to_users_table()
