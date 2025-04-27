import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'scantext.db')  # <-- вот правильный путь

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Теперь запрос к реальной базе:
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Таблицы в базе:", tables)

cursor.execute("SELECT * FROM payments WHERE user_id = 7;")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
