import os
from typing import Dict, Optional, List
from ..database.book_db import BookDatabase
import re
import tempfile

class TXTImporter:
    def __init__(self, db: BookDatabase):
        """Initialize the TXT importer service"""
        self.db = db
    
    def import_txt(self, txt_path: str, title: Optional[str] = None, 
                   author: Optional[str] = None, isbn: Optional[str] = None) -> Dict:
        """Import a TXT file into the database"""
        try:
            # Read the text file
            with open(txt_path, 'r', encoding='utf-8') as file:
                full_text = file.read()
            
            # Clean up the text
            full_text = self._clean_text(full_text)
            
            # Split into chapters if possible
            chapters = self._split_into_chapters(full_text)
            
            # Count words
            word_count = len(full_text.split())
            
            # Add to database
            book_id = self.db.add_book(
                title=title or os.path.splitext(os.path.basename(txt_path))[0],
                author=author or 'Unknown Author',
                content=full_text,
                isbn=isbn,
                description='',
                metadata={
                    'txt_path': txt_path,
                    'word_count': word_count,
                    'import_date': '',
                    'keywords': ''
                }
            )
            
            return {
                'book_id': book_id,
                'title': title,
                'author': author,
                'word_count': word_count,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def import_txt_from_bytes(self, txt_bytes: bytes, title: str, 
                            author: str, isbn: Optional[str] = None) -> Dict:
        """Import a TXT from bytes (useful for uploaded files)"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_file.write(txt_bytes)
                temp_path = temp_file.name
            
            # Import the temporary file
            result = self.import_txt(temp_path, title, author, isbn)
            
            # Clean up
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean up text content"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Persian characters
        text = re.sub(r'[^\w\s\u0600-\u06FF\uFB8A\u067E\u0686\u06AF]', '', text)
        
        # Fix common text issues
        text = text.replace('٠', '0')
        text = text.replace('١', '1')
        text = text.replace('٢', '2')
        text = text.replace('٣', '3')
        text = text.replace('٤', '4')
        text = text.replace('٥', '5')
        text = text.replace('٦', '6')
        text = text.replace('٧', '7')
        text = text.replace('٨', '8')
        text = text.replace('٩', '9')
        
        return text.strip()
    
    def _split_into_chapters(self, text: str) -> List[str]:
        """Split text into chapters based on common patterns"""
        # Common chapter patterns in Persian and English
        chapter_patterns = [
            r'فصل\s+\d+',
            r'Chapter\s+\d+',
            r'بخش\s+\d+',
            r'باب\s+\d+',
            r'قسمت\s+\d+',
            r'^\d+\.',  # Numbered sections
            r'^\d+\)',  # Numbered sections with parenthesis
            r'^[IVX]+\.',  # Roman numerals
            r'^[A-Z]\.'  # Letter sections
        ]
        
        # Combine patterns
        pattern = '|'.join(chapter_patterns)
        
        # Split text into chapters
        chapters = re.split(f'({pattern})', text)
        
        # Clean up chapters
        cleaned_chapters = []
        current_chapter = []
        
        for part in chapters:
            if re.match(pattern, part):
                if current_chapter:
                    cleaned_chapters.append('\n'.join(current_chapter))
                current_chapter = [part]
            else:
                current_chapter.append(part)
        
        if current_chapter:
            cleaned_chapters.append('\n'.join(current_chapter))
        
        return cleaned_chapters
    
    def extract_metadata(self, txt_path: str) -> Dict:
        """Extract metadata from TXT file"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Get first few lines for preview
            preview_lines = content.split('\n')[:5]
            preview_text = '\n'.join(preview_lines)
            
            # Count words
            word_count = len(content.split())
            
            return {
                'title': '',
                'author': '',
                'word_count': word_count,
                'preview': preview_text
            }
            
        except Exception as e:
            return {
                'error': str(e)
            } 