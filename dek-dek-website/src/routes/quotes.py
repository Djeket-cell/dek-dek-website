import json
import os
from flask import Blueprint, jsonify

quotes_bp = Blueprint('quotes', __name__)

def load_quotes_data():
    """Load quotes data from JSON file"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'quotes.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading quotes data: {e}")
        return []

@quotes_bp.route('/quotes', methods=['GET'])
def get_quotes():
    """Get all quotes"""
    try:
        quotes = load_quotes_data()
        return jsonify({
            'success': True,
            'data': quotes,
            'count': len(quotes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@quotes_bp.route('/quotes/<int:quote_id>', methods=['GET'])
def get_quote(quote_id):
    """Get a specific quote by ID"""
    try:
        quotes = load_quotes_data()
        quote = next((q for q in quotes if q['id'] == quote_id), None)
        
        if not quote:
            return jsonify({
                'success': False,
                'error': 'Quote not found'
            }), 404
            
        return jsonify({
            'success': True,
            'data': quote
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@quotes_bp.route('/quotes/random', methods=['GET'])
def get_random_quote():
    """Get a random quote"""
    try:
        import random
        quotes = load_quotes_data()
        
        if not quotes:
            return jsonify({
                'success': False,
                'error': 'No quotes available'
            }), 404
            
        random_quote = random.choice(quotes)
        return jsonify({
            'success': True,
            'data': random_quote
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

