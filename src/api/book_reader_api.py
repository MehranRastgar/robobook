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
from ..services.translation_service import TranslationService
import time

book_reader_bp = Blueprint('book_reader', __name__)

# Initialize services with correct database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'books.db')
db = BookDatabase(db_path)
reader = BookReader(api_key=os.getenv('OPENAI_API_KEY'), db=db)
pdf_importer = PDFImporter(db)
text_processor = TextProcessor()
tts_service = TTSService()
translation_service = TranslationService()

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

@book_reader_bp.route('/api/books/<int:book_id>/tts/<int:page_number>', methods=['GET'])
def get_page_audio(book_id, page_number):
    """Generate and return audio for a specific page."""
    try:
        book = db.get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404

        if 'processed_chunks' not in book:
            return jsonify({"error": "Book not processed yet"}), 400

        # Get the requested page
        chunks = book['processed_chunks']
        page = next((chunk for chunk in chunks if chunk['page_number'] == page_number), None)
        
        if not page:
            return jsonify({"error": "Page not found"}), 404

        # Generate audio for the page content
        audio_data = tts_service.text_to_speech(page['content'])

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Send the audio file
        return send_file(
            temp_file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'page_{page_number}.mp3'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

@book_reader_bp.route('/api/books/<int:book_id>/translate/<int:page_number>', methods=['POST'])
def translate_page(book_id, page_number):
    try:
        # Get the page content
        page_content = db.get_page_content(book_id, page_number)
        if not page_content:
            return jsonify({'error': 'Page not found'}), 404

        # Translate the content
        translated_content = translation_service.translate_to_farsi(page_content['content'])

        return jsonify({
            'translated_content': translated_content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@book_reader_bp.route('/api/books/<int:book_id>/process-translation', methods=['POST'])
def process_book_translation(book_id):
    """Process and translate chunks of a book to Farsi."""
    try:
        # Get the book from database
        book = db.get_book(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404

        if not book.get('processed_chunks'):
            return jsonify({'error': 'Book has not been processed yet'}), 400

        # Get translation parameters from request
        data = request.get_json() or {}
        start_page = data.get('start_page', 1)
        pages_to_translate = data.get('pages', None)  # None means translate all remaining pages
        
        # Validate parameters
        if start_page < 1:
            return jsonify({'error': 'Start page must be greater than 0'}), 400
            
        if pages_to_translate is not None and pages_to_translate < 1:
            return jsonify({'error': 'Number of pages must be greater than 0'}), 400

        # Filter chunks based on page range
        all_chunks = book['processed_chunks']
        start_idx = next((i for i, chunk in enumerate(all_chunks) 
                         if chunk['page_number'] == start_page), None)
        
        if start_idx is None:
            return jsonify({'error': f'Start page {start_page} not found'}), 404
            
        # Calculate end index based on pages_to_translate
        if pages_to_translate is not None:
            end_idx = min(start_idx + pages_to_translate, len(all_chunks))
        else:
            end_idx = len(all_chunks)
            
        chunks_to_translate = all_chunks[start_idx:end_idx]
        total_chunks = len(chunks_to_translate)
        
        if total_chunks == 0:
            return jsonify({'error': 'No pages to translate in the specified range'}), 400

        # Process each chunk
        translated_chunks = []
        start_time = time.time()
        
        print(f"\nStarting translation of book: {book['title']}")
        print(f"Translating pages {start_page} to {start_page + total_chunks - 1}")
        print(f"Total chunks to translate: {total_chunks}")
        print("=" * 50)
        
        for i, chunk in enumerate(chunks_to_translate, 1):
            try:
                chunk_start_time = time.time()
                
                # Translate the chunk content with book title context
                translated_content = translation_service.translate_to_farsi(
                    chunk['content'],
                    book_title=book['title']
                )
                
                # Create translated chunk with only the fields we have
                translated_chunk = {
                    'content': translated_content,
                    'page_number': chunk['page_number'],
                    'offset': chunk.get('offset', i - 1)  # Use index as offset if not present
                }
                translated_chunks.append(translated_chunk)
                
                # Calculate progress and time estimates
                progress = (i / total_chunks) * 100
                elapsed_time = time.time() - start_time
                avg_time_per_chunk = elapsed_time / i
                remaining_chunks = total_chunks - i
                estimated_time_remaining = remaining_chunks * avg_time_per_chunk
                
                # Calculate chunk processing time
                chunk_time = time.time() - chunk_start_time
                
                # Print detailed progress
                print(f"\nChunk {i}/{total_chunks} ({progress:.1f}%)")
                print(f"Page: {chunk['page_number']}")
                print(f"Processing time: {chunk_time:.2f} seconds")
                print(f"Average time per chunk: {avg_time_per_chunk:.2f} seconds")
                print(f"Estimated time remaining: {estimated_time_remaining/60:.1f} minutes")
                print("-" * 30)
                
            except Exception as e:
                print(f"\nError translating chunk {i}: {str(e)}")
                print(f"Chunk data: {chunk}")  # Add this line to debug chunk structure
                continue

        # Create new translated version in database
        translated_book_id = db.create_translated_version(
            book_id,
            translated_chunks,
            'fa',  # Farsi language code
            translation_service.model  # Pass the model name
        )

        if not translated_book_id:
            return jsonify({'error': 'Failed to create translated version'}), 500

        # Print final summary
        total_time = time.time() - start_time
        print("\nTranslation completed!")
        print(f"Total time taken: {total_time/60:.1f} minutes")
        print(f"Average time per chunk: {total_time/total_chunks:.2f} seconds")
        print(f"Model used: {translation_service.model}")
        print("=" * 50)

        return jsonify({
            'message': 'Translation completed successfully',
            'translated_book_id': translated_book_id,
            'total_time': f"{total_time/60:.1f} minutes",
            'total_chunks': total_chunks,
            'start_page': start_page,
            'end_page': start_page + total_chunks - 1
        })

    except Exception as e:
        print(f"\nTranslation processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500