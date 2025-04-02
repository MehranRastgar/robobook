import sqlite3

conn = sqlite3.connect('books.db')
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(books)")
existing_columns = [column[1] for column in cursor.fetchall()]

# Add columns only if they don't exist
columns_to_add = [
    ('is_translation', 'BOOLEAN DEFAULT 0'),
    ('original_book_id', 'INTEGER'),
    ('translation_language', 'TEXT'),
    ('translation_model', 'TEXT')
]

for column_name, column_type in columns_to_add:
    if column_name not in existing_columns:
        print(f"Adding column: {column_name}")
        cursor.execute(f"ALTER TABLE books ADD COLUMN {column_name} {column_type}")

# Add foreign key constraint if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS books_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        isbn TEXT,
        text_content TEXT,
        processed_chunks TEXT,
        total_pages INTEGER,
        is_translation BOOLEAN DEFAULT 0,
        original_book_id INTEGER,
        translation_language TEXT,
        translation_model TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (original_book_id) REFERENCES books (id)
    )
""")

# Copy data from old table to new table
cursor.execute("""
    INSERT INTO books_new 
    SELECT id, title, author, isbn, text_content, processed_chunks, total_pages, 
           is_translation, original_book_id, translation_language, translation_model, created_at
    FROM books
""")

# Drop old table and rename new table
cursor.execute("DROP TABLE books")
cursor.execute("ALTER TABLE books_new RENAME TO books")

conn.commit()
conn.close() 