import sqlite3

DB = "study_app.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Check if box column exists
cur.execute("PRAGMA table_info(flashcards);")
cols = [row[1] for row in cur.fetchall()]
print("Existing columns:", cols)

if "box_number" in cols and "box" not in cols:
    print("Renaming box_number -> box...")
    cur.execute("ALTER TABLE flashcards RENAME TO flashcards_old;")
    cur.execute("""
        CREATE TABLE flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            question TEXT,
            answer TEXT,
            box INTEGER DEFAULT 1,
            last_reviewed TEXT,
            mistakes INTEGER DEFAULT 0
        );
    """)
    cur.execute("""
        INSERT INTO flashcards (id, subject, question, answer, box, last_reviewed, mistakes)
        SELECT id, subject, question, answer, box_number, last_reviewed, mistakes
        FROM flashcards_old;
    """)
    cur.execute("DROP TABLE flashcards_old;")
    conn.commit()
    print("Migration complete ✅")
else:
    print("No migration needed.")

conn.close()
