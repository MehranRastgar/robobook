import sqlite3
import json
import os
from typing import List, Dict, Optional, Any

class BookDatabase:
    def __init__(self, db_path: str):
        """Initialize the database with the given path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_book_id) REFERENCES books (id)
            )
        ''')

        # Check if processed_chunks column exists, if not add it
        cursor.execute("PRAGMA table_info(books)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'processed_chunks' not in columns:
            cursor.execute('ALTER TABLE books ADD COLUMN processed_chunks TEXT')
            cursor.execute('ALTER TABLE books ADD COLUMN total_pages INTEGER')

        # Create chapters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_number INTEGER,
                title TEXT,
                content TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')

        # Create bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_id INTEGER,
                position INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (chapter_id) REFERENCES chapters (id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_book(self, title: str, author: str = None, isbn: str = None, text_content: str = None) -> int:
        """Add a new book to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books (title, author, isbn, text_content)
            VALUES (?, ?, ?, ?)
        ''', (title, author, isbn, text_content))
        
        book_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return book_id

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get a book by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM books WHERE id = ?
        ''', (book_id,))
        
        book = cursor.fetchone()
        if not book:
            conn.close()
            return None
            
        # Get chapters
        cursor.execute('''
            SELECT * FROM chapters WHERE book_id = ?
            ORDER BY chapter_number
        ''', (book_id,))
        
        chapters = cursor.fetchall()
        
        # Convert to dictionary
        book_dict = {
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'isbn': book[3],
            'text_content': book[4],
            'processed_chunks': json.loads(book[5]) if book[5] else None,
            'total_pages': book[6],
            'created_at': book[7]
        }
        
        if chapters:
            book_dict['chapters'] = [
                {
                    'id': ch[0],
                    'chapter_number': ch[2],
                    'title': ch[3],
                    'content': ch[4]
                }
                for ch in chapters
            ]
        
        conn.close()
        return book_dict

    def update_book(self, book_id: int, data: Dict[str, Any]) -> bool:
        """Update a book's data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert processed_chunks to JSON if present
        if 'processed_chunks' in data:
            data['processed_chunks'] = json.dumps(data['processed_chunks'])
        
        # Build update query
        update_fields = []
        values = []
        for key, value in data.items():
            update_fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(book_id)
        
        query = f'''
            UPDATE books 
            SET {', '.join(update_fields)}
            WHERE id = ?
        '''
        
        cursor.execute(query, values)
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success

    def search_books(self, query: str) -> List[Dict[str, Any]]:
        """Search books by title or author."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%'))
        
        books = cursor.fetchall()
        
        # Convert to list of dictionaries
        books_list = []
        for book in books:
            book_dict = {
                'id': book[0],
                'title': book[1],
                'author': book[2],
                'isbn': book[3],
                'text_content': book[4],
                'processed_chunks': json.loads(book[5]) if book[5] else None,
                'total_pages': book[6],
                'created_at': book[7]
            }
            books_list.append(book_dict)
        
        conn.close()
        return books_list

    def add_chapter(self, book_id: int, chapter_number: int, title: str, content: str) -> int:
        """Add a chapter to a book."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chapters (book_id, chapter_number, title, content)
            VALUES (?, ?, ?, ?)
        ''', (book_id, chapter_number, title, content))
        
        chapter_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return chapter_id

    def get_bookmarks(self, book_id: int) -> List[Dict[str, Any]]:
        """Get all bookmarks for a book."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, c.chapter_number, c.title as chapter_title
            FROM bookmarks b
            JOIN chapters c ON b.chapter_id = c.id
            WHERE b.book_id = ?
            ORDER BY b.created_at DESC
        ''', (book_id,))
        
        bookmarks = cursor.fetchall()
        
        # Convert to list of dictionaries
        bookmarks_list = [
            {
                'id': b[0],
                'book_id': b[1],
                'chapter_id': b[2],
                'position': b[3],
                'note': b[4],
                'created_at': b[5],
                'chapter_number': b[6],
                'chapter_title': b[7]
            }
            for b in bookmarks
        ]
        
        conn.close()
        return bookmarks_list

    def add_bookmark(self, book_id: int, chapter_id: int, position: int, note: str = None) -> int:
        """Add a bookmark to a book."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookmarks (book_id, chapter_id, position, note)
            VALUES (?, ?, ?, ?)
        ''', (book_id, chapter_id, position, note))
        
        bookmark_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return bookmark_id

    def get_page_content(self, book_id: int, page_number: int) -> dict:
        """
        Get the content of a specific page from a book.
        
        Args:
            book_id (int): The ID of the book
            page_number (int): The page number to retrieve
            
        Returns:
            dict: A dictionary containing the page content and metadata
        """
        try:
            book = self.get_book(book_id)
            if not book:
                return None

            if not book.get('processed_chunks'):
                return None

            # Find the chunk with the matching page number
            page = next((chunk for chunk in book['processed_chunks'] 
                        if chunk['page_number'] == page_number), None)
            
            if not page:
                return None

            return {
                'content': page['content'],
                'page_number': page_number,
                'total_pages': book['total_pages']
            }
        except Exception as e:
            print(f"Error getting page content: {str(e)}")
            return None

    def create_translated_version(self, original_book_id: int, translated_chunks: List[Dict], language: str, model: str) -> int:
        """
        Create a new translated version of a book.
        
        Args:
            original_book_id (int): ID of the original book
            translated_chunks (List[Dict]): List of translated chunks
            language (str): Language code of the translation
            model (str): Name of the OpenAI model used for translation
            
        Returns:
            int: ID of the new translated book
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get original book details
        original_book = self.get_book(original_book_id)
        if not original_book:
            conn.close()
            return None
            
        # Create new book entry for translation
        cursor.execute('''
            INSERT INTO books (
                title, author, isbn, processed_chunks, total_pages,
                is_translation, original_book_id, translation_language, translation_model
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
        ''', (
            f"{original_book['title']} ({language})",
            original_book['author'],
            original_book['isbn'],
            json.dumps(translated_chunks),
            original_book['total_pages'],
            original_book_id,
            language,
            model
        ))
        
        translated_book_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return translated_book_id

    def get_translated_versions(self, book_id: int) -> List[Dict]:
        """
        Get all translated versions of a book.
        
        Args:
            book_id (int): ID of the original book
            
        Returns:
            List[Dict]: List of translated book versions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE original_book_id = ? AND is_translation = 1
            ORDER BY created_at DESC
        ''', (book_id,))
        
        translations = cursor.fetchall()
        
        # Convert to list of dictionaries
        translations_list = []
        for trans in translations:
            trans_dict = {
                'id': trans[0],
                'title': trans[1],
                'author': trans[2],
                'isbn': trans[3],
                'text_content': trans[4],
                'processed_chunks': json.loads(trans[5]) if trans[5] else None,
                'total_pages': trans[6],
                'is_translation': trans[7],
                'original_book_id': trans[8],
                'translation_language': trans[9],
                'created_at': trans[10]
            }
            translations_list.append(trans_dict)
        
        conn.close()
        return translations_list 