import PyPDF2
import io
import os
from typing import Dict, Optional, List
from ..database.book_db import BookDatabase
import fitz  # PyMuPDF for better PDF handling
import re

class PDFImporter:
    def __init__(self, db: BookDatabase):
        """Initialize the PDF importer service"""
        self.db = db
    
    def import_pdf(self, pdf_path: str, title: Optional[str] = None, 
                   author: Optional[str] = None, isbn: Optional[str] = None) -> Dict:
        """Import a PDF file into the database"""
        try:
            # Open PDF with PyMuPDF for better text extraction
            doc = fitz.open(pdf_path)
            
            # Extract metadata if available
            metadata = doc.metadata
            if not title:
                title = metadata.get('title', os.path.splitext(os.path.basename(pdf_path))[0])
            if not author:
                author = metadata.get('author', 'Unknown Author')
            
            # Extract text from all pages
            text_content = []
            for page in doc:
                text_content.append(page.get_text())
            
            # Join all text with proper spacing
            full_text = '\n\n'.join(text_content)
            
            # Clean up the text
            full_text = self._clean_text(full_text)
            
            # Split into chapters if possible
            chapters = self._split_into_chapters(full_text)
            
            # Get page count before closing
            page_count = len(doc)
            
            # Add to database
            book_id = self.db.add_book(
                title=title,
                author=author,
                text_content=full_text,
                isbn=isbn
            )
            
            # Close document after we're done using it
            doc.close()
            
            return {
                'book_id': book_id,
                'title': title,
                'author': author,
                'page_count': page_count,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def import_pdf_from_bytes(self, pdf_bytes: bytes, title: str, 
                            author: str, isbn: Optional[str] = None) -> Dict:
        """Import a PDF from bytes (useful for uploaded files)"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_path = temp_file.name
            
            # Import the temporary file
            result = self.import_pdf(temp_path, title, author, isbn)
            
            # Clean up
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean up extracted text"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Persian characters
        text = re.sub(r'[^\w\s\u0600-\u06FF\uFB8A\u067E\u0686\u06AF]', '', text)
        
        # Fix common OCR issues
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
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Extract text from first page for potential description
            first_page = doc[0]
            preview_text = first_page.get_text()[:500]  # First 500 chars
            
            doc.close()
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'keywords': metadata.get('keywords', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'preview': preview_text
            }
            
        except Exception as e:
            return {
                'error': str(e)
            } 