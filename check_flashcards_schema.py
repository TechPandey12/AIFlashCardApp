import sqlite3

# Connect to your main DB
conn = sqlite3.connect("study_app.db")
cur = conn.cursor()

# List tables
print("Tables in DB:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

# Show flashcards table schema
print("\nFlashcards schema:")
cur.execute("PRAGMA table_info(flashcards);")
for row in cur.fetchall():
    print(row)

conn.close()
