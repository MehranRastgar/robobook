from flask import Blueprint, request, jsonify
from ..services.book_reader import BookReader
from ..services.pdf_importer import PDFImporter
from ..database.book_db import BookDatabase
import os
from werkzeug.utils import secure_filename
from ..services.txt_importer import TXTImporter
import tempfile

book_reader_bp = Blueprint('book_reader', __name__)

# Initialize services
db = BookDatabase()
reader = BookReader(api_key=os.getenv('OPENAI_API_KEY'), db=db)
pdf_importer = PDFImporter(db)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@book_reader_bp.route('/api/books/import/pdf', methods=['POST'])
def import_pdf():
    """Import a PDF file into the database"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Get metadata from form data
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Import PDF
        result = pdf_importer.import_pdf(filepath, title, author, isbn)
        
        # Clean up
        os.remove(filepath)
        
        if result.get('status') == 'error':
            return jsonify({'error': result['error']}), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@book_reader_bp.route('/api/books/import/pdf/metadata', methods=['POST'])
def extract_pdf_metadata():
    """Extract metadata from a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Extract metadata
        metadata = pdf_importer.extract_metadata(filepath)
        
        # Clean up
        os.remove(filepath)
        
        if 'error' in metadata:
            return jsonify({'error': metadata['error']}), 500
        
        return jsonify(metadata)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@book_reader_bp.route('/api/books', methods=['GET'])
def get_books():
    """Get all books or search books"""
    query = request.args.get('q', '')
    if query:
        books = db.search_books(query)
    else:
        books = db.search_books('')  # Get all books
    return jsonify(books)

@book_reader_bp.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get book details"""
    book = db.get_book(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book)

@book_reader_bp.route('/api/books/<int:book_id>/chapters/<int:chapter_number>', methods=['GET'])
def get_chapter(book_id, chapter_number):
    """Get chapter content with AI enhancements"""
    result = reader.read_chapter(book_id, chapter_number)
    if not result:
        return jsonify({'error': 'Chapter not found'}), 404
    return jsonify(result)

@book_reader_bp.route('/api/books/<int:book_id>/ask', methods=['POST'])
def ask_question(book_id):
    """Ask a question about the book"""
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400
    
    context = data.get('context')
    answer = reader.ask_question(book_id, data['question'], context)
    return jsonify({'answer': answer})

@book_reader_bp.route('/api/books/<int:book_id>/chapters/<int:chapter_number>/summary', methods=['GET'])
def get_chapter_summary(book_id, chapter_number):
    """Get AI-generated chapter summary"""
    summary = reader.summarize_chapter(book_id, chapter_number)
    if not summary:
        return jsonify({'error': 'Chapter not found'}), 404
    return jsonify({'summary': summary})

@book_reader_bp.route('/api/books/<int:book_id>/themes', methods=['GET'])
def get_book_themes(book_id):
    """Get AI analysis of book themes"""
    analysis = reader.analyze_theme(book_id)
    if not analysis:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(analysis)

@book_reader_bp.route('/api/books/<int:book_id>/bookmarks', methods=['GET'])
def get_bookmarks(book_id):
    """Get bookmarks for a book"""
    bookmarks = db.get_bookmarks(book_id)
    return jsonify(bookmarks)

@book_reader_bp.route('/api/books/<int:book_id>/bookmarks', methods=['POST'])
def add_bookmark(book_id):
    """Add a bookmark to a book"""
    data = request.get_json()
    if not data or 'chapter_id' not in data or 'position' not in data:
        return jsonify({'error': 'Chapter ID and position are required'}), 400
    
    bookmark_id = db.add_bookmark(
        book_id=book_id,
        chapter_id=data['chapter_id'],
        position=data['position'],
        note=data.get('note')
    )
    return jsonify({'bookmark_id': bookmark_id})

@book_reader_bp.route('/api/books/import/txt', methods=['POST'])
def import_txt():
    """Import a TXT file into the database"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Read the uploaded file
        content = file.read()
        
        # Initialize TXT importer
        txt_importer = TXTImporter(db)
        
        # Import the TXT file
        result = txt_importer.import_txt_from_bytes(
            content,
            title=request.form.get('title') or file.filename,
            author=request.form.get('author') or 'Unknown Author',
            isbn=request.form.get('isbn')
        )
        
        if result.get('status') == 'error':
            return jsonify({'error': result['error']}), 400
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@book_reader_bp.route('/api/books/import/txt/metadata', methods=['POST'])
def extract_txt_metadata():
    """Extract metadata from a TXT file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            content = file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Initialize TXT importer
        txt_importer = TXTImporter(db)
        
        # Extract metadata
        metadata = txt_importer.extract_metadata(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        if 'error' in metadata:
            return jsonify({'error': metadata['error']}), 400
            
        return jsonify(metadata)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 