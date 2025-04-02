from flask import Flask, request, jsonify
from dataset_loader import USPDBooks
import logging
from typing import Optional
import random

app = Flask(__name__)
books_db = USPDBooks()

@app.route('/api/books/random', methods=['GET'])
def get_random_books():
    """Get random books endpoint"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # Validate limit
        if limit < 1 or limit > 100:
            return jsonify({
                'status': 'error',
                'error': 'Limit must be between 1 and 100'
            }), 400
        
        # Get random books
        results = books_db.get_random_books(limit=limit)
        
        return jsonify({
            'status': 'success',
            'count': len(results),
            'books': results
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/books/search', methods=['GET'])
def search_books():
    """Search books endpoint"""
    try:
        # Get search parameters with defaults
        title = request.args.get('title')
        author = request.args.get('author')
        year = request.args.get('year')
        limit = int(request.args.get('limit', 10))
        min_year = request.args.get('min_year')
        max_year = request.args.get('max_year')
        sort_by = request.args.get('sort_by', 'relevance')  # relevance, year, title
        
        # Convert year parameters to integers
        if year:
            year = int(year)
        if min_year:
            min_year = int(min_year)
        if max_year:
            max_year = int(max_year)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            return jsonify({
                'status': 'error',
                'error': 'Limit must be between 1 and 100'
            }), 400
            
        if year and (year < 1800 or year > 2024):
            return jsonify({
                'status': 'error',
                'error': 'Year must be between 1800 and 2024'
            }), 400
            
        if min_year and max_year and min_year > max_year:
            return jsonify({
                'status': 'error',
                'error': 'Minimum year cannot be greater than maximum year'
            }), 400
        
        # Create search parameters dictionary
        search_params = {
            'title': title,
            'author': author,
            'year': year,
            'limit': limit,
            'sort_by': sort_by
        }
        
        # Add optional year range parameters if they exist
        if min_year is not None:
            search_params['min_year'] = min_year
        if max_year is not None:
            search_params['max_year'] = max_year
        
        # Perform search
        results = books_db.search_books(**search_params)
        
        return jsonify({
            'status': 'success',
            'count': len(results),
            'books': results,
            'search_params': search_params
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': f'Invalid parameter value: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/books/<ocaid>', methods=['GET'])
def get_book(ocaid):
    """Get book content endpoint"""
    try:
        book = books_db.get_book_content(ocaid)
        if not book:
            return jsonify({
                'status': 'error',
                'error': 'Book not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'book': book
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/books/stats', methods=['GET'])
def get_stats():
    """Get dataset statistics"""
    try:
        stats = books_db.get_dataset_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Load dataset on startup
    books_db.load_dataset()
    app.run(debug=True) 