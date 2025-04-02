from flask import Blueprint, request, jsonify, send_file
from ..services.book_reader import BookReader
from ..services.pdf_importer import PDFImporter
from ..database.book_db import BookDatabase
import os
from werkzeug.utils import secure_filename
from ..services.txt_importer import TXTImporter
import tempfile
from ..services.text_processor import TextProcessor
from ..services.tts_service import TTSService

book_reader_bp = Blueprint('book_reader', __name__)

# Initialize services with correct database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'books.db')
db = BookDatabase(db_path)
reader = BookReader(api_key=os.getenv('OPENAI_API_KEY'), db=db)
pdf_importer = PDFImporter(db)
text_processor = TextProcessor()
tts_service = TTSService()

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@book_reader_bp.route('/api/books/<int:book_id>/process', methods=['POST'])
def process_book(book_id):
    """Process a book's content into chunks of 1000 characters each."""
    try:
        book = db.get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Get the book's content
        content = ""
        if book.get('chapters'):
            content = "\n".join(chapter['content'] for chapter in book['chapters'])
        elif book.get('text_content'):
            content = book['text_content']
        else:
            return jsonify({"error": "No content found in book"}), 400

        # Process the content into chunks of 1000 characters
        chunk_size = 1000
        chunks = []
        total_length = len(content)
        
        for i in range(0, total_length, chunk_size):
            chunk = content[i:i + chunk_size]
            chunks.append({
                'offset': i,
                'content': chunk,
                'page_number': len(chunks) + 1
            })
        
        # Store processed chunks in database
        db.update_book(book_id, {
            'processed_chunks': chunks,
            'total_pages': len(chunks)
        })

        return jsonify({
            "message": "Book processed successfully",
            "total_pages": len(chunks)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@book_reader_bp.route('/api/books/<int:book_id>/page/<int:page_number>', methods=['GET'])
def get_book_page(book_id, page_number):
    """Get a specific page of the processed book."""
    try:
        # Get book from database
        book = db.get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Check if book has been processed
        if not book.get('processed_chunks'):
            return jsonify({
                "error": "Book not processed yet",
                "message": "Please process the book first using /api/books/{book_id}/process endpoint"
            }), 400

        # Get the requested page
        chunks = book['processed_chunks']
        page = next((chunk for chunk in chunks if chunk['page_number'] == page_number), None)
        
        if not page:
            return jsonify({"error": "Page not found"}), 404

        return jsonify({
            "page_number": page_number,
            "content": page['content'],
            "total_pages": book['total_pages']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Keep all other existing routes and functions
// ... existing code ...