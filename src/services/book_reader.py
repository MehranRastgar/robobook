from typing import Dict, List, Optional
from openai import OpenAI
import json
from ..database.book_db import BookDatabase

class BookReader:
    def __init__(self, api_key: str, db: BookDatabase):
        """Initialize the book reader service"""
        self.openai_client = OpenAI(api_key=api_key)
        self.db = db
    
    def read_chapter(self, book_id: int, chapter_number: int) -> Dict:
        """Read a chapter and generate AI-enhanced content"""
        chapter = self.db.get_chapter(book_id, chapter_number)
        if not chapter:
            return None
        
        # Get book details for context
        book = self.db.get_book(book_id)
        
        # Generate AI-enhanced content
        enhanced_content = self._enhance_content(
            chapter['content'],
            book['title'],
            book['author']
        )
        
        return {
            'chapter': chapter,
            'enhanced_content': enhanced_content
        }
    
    def ask_question(self, book_id: int, question: str, context: Optional[str] = None) -> str:
        """Ask a question about the book content"""
        # Get relevant context if not provided
        if not context:
            book = self.db.get_book(book_id)
            context = book['text_content'][:2000]  # First 2000 chars for context
        
        # Generate AI response
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful book assistant. Answer questions about the book content accurately and concisely."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def summarize_chapter(self, book_id: int, chapter_number: int) -> str:
        """Generate a summary of a chapter"""
        chapter = self.db.get_chapter(book_id, chapter_number)
        if not chapter:
            return None
        
        # Generate AI summary
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful book assistant. Create a concise summary of the chapter."},
                {"role": "user", "content": f"Chapter content: {chapter['content']}"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content
    
    def analyze_theme(self, book_id: int) -> Dict:
        """Analyze themes and topics in the book"""
        book = self.db.get_book(book_id)
        if not book:
            return None
        
        # Generate AI analysis
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a literary analyst. Analyze the main themes and topics in the book."},
                {"role": "user", "content": f"Book content: {book['text_content'][:4000]}"}  # First 4000 chars for analysis
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            'analysis': response.choices[0].message.content,
            'book_title': book['title'],
            'book_author': book['author']
        }
    
    def _enhance_content(self, content: str, book_title: str, author: str) -> Dict:
        """Enhance book content with AI-generated features"""
        # Generate character analysis
        characters = self._analyze_characters(content)
        
        # Generate key points
        key_points = self._extract_key_points(content)
        
        # Generate vocabulary list
        vocabulary = self._extract_vocabulary(content)
        
        return {
            'original_content': content,
            'characters': characters,
            'key_points': key_points,
            'vocabulary': vocabulary
        }
    
    def _analyze_characters(self, content: str) -> List[Dict]:
        """Analyze characters mentioned in the content"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract and analyze characters mentioned in the text. Return as JSON array."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return []
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from the content"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract key points from the text. Return as JSON array."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return []
    
    def _extract_vocabulary(self, content: str) -> List[Dict]:
        """Extract vocabulary words and their meanings"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract vocabulary words and their meanings. Return as JSON array."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return [] 