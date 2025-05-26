import sqlite3

conn = sqlite3.connect('veritabani.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_approved INTEGER DEFAULT 0,
    first_login INTEGER DEFAULT 1
)
''')

conn.commit()
conn.close()

print("Veritabanı ve users tablosu oluşturuldu.")
