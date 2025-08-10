from db import db_get_connection

def main():
    conn = db_get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(messages);")
    columns = [row[1] for row in cursor.fetchall()]
    if "effort" not in columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN effort TEXT;")
        conn.commit()
        print("Added 'effort' column to messages table.")
    else:
        print("'effort' column already exists in messages table.")

if __name__ == "__main__":
    main()
