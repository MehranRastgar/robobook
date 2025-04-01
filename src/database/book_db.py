import sqlite3
import json
from typing import List, Dict, Optional
import os

class BookDatabase:
    def __init__(self, db_path: str = "books.db"):
        """Initialize the book database"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE,
                description TEXT,
                cover_image TEXT,
                text_content TEXT,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create chapters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                chapter_number INTEGER,
                title TEXT,
                content TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id),
                UNIQUE(book_id, chapter_number)
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
    
    def add_book(self, title: str, author: str, content: str, 
                 isbn: Optional[str] = None, description: Optional[str] = None,
                 cover_image: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Add a new book to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO books (title, author, isbn, description, cover_image, text_content, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, isbn, description, cover_image, content, 
                 json.dumps(metadata) if metadata else None))
            
            book_id = cursor.lastrowid
            
            # Split content into chapters
            chapters = self._split_into_chapters(content)
            for i, chapter in enumerate(chapters, 1):
                cursor.execute('''
                    INSERT INTO chapters (book_id, chapter_number, content)
                    VALUES (?, ?, ?)
                ''', (book_id, i, chapter))
            
            conn.commit()
            return book_id
            
        finally:
            conn.close()
    
    def get_book(self, book_id: int) -> Optional[Dict]:
        """Get book details and content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, title, author, isbn, description, cover_image, text_content, metadata
                FROM books WHERE id = ?
            ''', (book_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'title': row[1],
                'author': row[2],
                'isbn': row[3],
                'description': row[4],
                'cover_image': row[5],
                'text_content': row[6],
                'metadata': json.loads(row[7]) if row[7] else None
            }
            
        finally:
            conn.close()
    
    def get_chapter(self, book_id: int, chapter_number: int) -> Optional[Dict]:
        """Get a specific chapter of a book"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, title, content
                FROM chapters
                WHERE book_id = ? AND chapter_number = ?
            ''', (book_id, chapter_number))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'title': row[1],
                'content': row[2]
            }
            
        finally:
            conn.close()
    
    def search_books(self, query: str) -> List[Dict]:
        """Search books by title, author, or content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, title, author, description, cover_image
                FROM books
                WHERE title LIKE ? OR author LIKE ? OR text_content LIKE ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            return [{
                'id': row[0],
                'title': row[1],
                'author': row[2],
                'description': row[3],
                'cover_image': row[4]
            } for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def add_bookmark(self, book_id: int, chapter_id: int, position: int, note: Optional[str] = None) -> int:
        """Add a bookmark to a book"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bookmarks (book_id, chapter_id, position, note)
                VALUES (?, ?, ?, ?)
            ''', (book_id, chapter_id, position, note))
            
            conn.commit()
            return cursor.lastrowid
            
        finally:
            conn.close()
    
    def get_bookmarks(self, book_id: int) -> List[Dict]:
        """Get all bookmarks for a book"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT b.id, b.chapter_id, b.position, b.note, b.created_at,
                       c.chapter_number, c.title
                FROM bookmarks b
                JOIN chapters c ON b.chapter_id = c.id
                WHERE b.book_id = ?
                ORDER BY b.created_at DESC
            ''', (book_id,))
            
            return [{
                'id': row[0],
                'chapter_id': row[1],
                'position': row[2],
                'note': row[3],
                'created_at': row[4],
                'chapter_number': row[5],
                'chapter_title': row[6]
            } for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def _split_into_chapters(self, content: str) -> List[str]:
        """Split book content into chapters"""
        # This is a simple implementation. You might want to make it more sophisticated
        # based on your book format and requirements
        chapters = []
        current_chapter = []
        
        for line in content.split('\n'):
            if line.strip().startswith('Chapter') or line.strip().startswith('فصل'):
                if current_chapter:
                    chapters.append('\n'.join(current_chapter))
                current_chapter = [line]
            else:
                current_chapter.append(line)
        
        if current_chapter:
            chapters.append('\n'.join(current_chapter))
        
        return chapters 