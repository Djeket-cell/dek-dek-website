import os
import sys
import json
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
           static_folder=os.path.join(BASE_DIR, 'src', 'static'),
           template_folder=os.path.join(BASE_DIR, 'src', 'static'))

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app)

# Configuration de l'application
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

@app.route('/')
def index():
    """Route principale - sert le fichier index.html"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Erreur lors du chargement de la page: {str(e)}", 500

@app.route('/<path:path>')
def serve_static(path):
    """Sert les fichiers statiques"""
    try:
        static_folder_path = app.static_folder
        if static_folder_path and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            # Si le fichier n'existe pas, retourner index.html (pour les SPA)
            return render_template('index.html')
    except Exception as e:
        return f"Fichier non trouvé: {path}", 404

@app.route('/api/books')
def get_books():
    """API pour récupérer la liste des livres"""
    try:
        books_path = os.path.join(BASE_DIR, 'data', 'books.json')
        with open(books_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
        return jsonify({
            'success': True,
            'data': books,
            'count': len(books)
        })
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Fichier books.json non trouvé'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/books/<int:book_id>')
def get_book(book_id):
    """API pour récupérer un livre spécifique"""
    try:
        books_path = os.path.join(BASE_DIR, 'data', 'books.json')
        with open(books_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
        
        book = next((b for b in books if b.get('id') == book_id), None)
        if not book:
            return jsonify({
                'success': False,
                'error': 'Livre non trouvé'
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

@app.route('/api/quotes')
def get_quotes():
    """API pour récupérer la liste des citations"""
    try:
        quotes_path = os.path.join(BASE_DIR, 'data', 'quotes.json')
        with open(quotes_path, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        return jsonify({
            'success': True,
            'data': quotes,
            'count': len(quotes)
        })
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Fichier quotes.json non trouvé'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Route de santé pour vérifier que l'application fonctionne"""
    return jsonify({
        "status": "OK", 
        "message": "Application déployée avec succès",
        "version": "1.0"
    })

# Point d'entrée pour le déploiement
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

