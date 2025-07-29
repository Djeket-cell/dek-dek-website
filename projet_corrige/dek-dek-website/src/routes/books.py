import json
import os
from flask import Blueprint, jsonify

books_bp = Blueprint('books', __name__)

def load_books_data():
    """Load books data from JSON file"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'books.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading books data: {e}")
        return []

@books_bp.route('/books', methods=['GET'])
def get_books():
    """Get all books"""
    try:
        books = load_books_data()
        return jsonify({
            'success': True,
            'data': books,
            'count': len(books)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@books_bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get a specific book by ID"""
    try:
        books = load_books_data()
        book = next((b for b in books if b['id'] == book_id), None)
        
        if not book:
            return jsonify({
                'success': False,
                'error': 'Book not found'
            }), 404
            
        return jsonify({
            'success': True,
            'data': book
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

