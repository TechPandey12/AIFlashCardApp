import sqlite3

# Connect (creates progress.db if it doesn't exist)
conn = sqlite3.connect("progress.db")
cursor = conn.cursor()

# Create the table
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accuracy FLOAT NOT NULL
);
""")

conn.commit()
conn.close()

print("✅ Database and table created successfully (progress.db)")
