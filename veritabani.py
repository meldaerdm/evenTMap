import sqlite3

conn = sqlite3.connect("veritabani.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               email TEXT UNİQUE NOT NULL,
               password TEXT NOT NULL,
               is_approved BOOLEAN DEFAULT 0,
               first_login INTEGER DEFAULT 1
               )
""")

conn.commit()
conn.close()

print("veritabanı ve 'users' tablosu oluşturuldu.")