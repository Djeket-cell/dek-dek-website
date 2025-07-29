import os
import sys
import json
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Initialisation de la base de données
db = SQLAlchemy()

# Modèle User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin
        }

app = Flask(__name__, 
           static_folder=os.path.join(BASE_DIR, 'src', 'static'),
           template_folder=os.path.join(BASE_DIR, 'src', 'static'))

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app)

# Configuration de l'application
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base de données
db.init_app(app)

# Création des tables
with app.app_context():
    db.create_all()

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

# ==================== API LIVRES ====================
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

# ==================== API CITATIONS ====================
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

# ==================== API UTILISATEURS (ADMINISTRATION) ====================
@app.route('/api/users', methods=['GET'])
def get_users():
    """Récupérer tous les utilisateurs"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'count': len(users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        data = request.json
        if not data or 'username' not in data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Username et email requis'
            }), 400
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur ou email déjà existant'
            }), 409
        
        user = User(
            username=data['username'], 
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'Utilisateur créé avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Récupérer un utilisateur spécifique"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
        
        data = request.json
        if data:
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            user.is_admin = data.get('is_admin', user.is_admin)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'Utilisateur mis à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Utilisateur supprimé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ROUTES ADMINISTRATEUR ====================
@app.route('/api/admin/stats')
def admin_stats():
    """Statistiques pour l'administration"""
    try:
        total_users = User.query.count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        # Compter les livres et citations
        books_path = os.path.join(BASE_DIR, 'data', 'books.json')
        quotes_path = os.path.join(BASE_DIR, 'data', 'quotes.json')
        
        total_books = 0
        total_quotes = 0
        
        try:
            with open(books_path, 'r', encoding='utf-8') as f:
                books = json.load(f)
                total_books = len(books)
        except:
            pass
            
        try:
            with open(quotes_path, 'r', encoding='utf-8') as f:
                quotes = json.load(f)
                total_quotes = len(quotes)
        except:
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'admin_users': admin_users,
                'regular_users': total_users - admin_users,
                'total_books': total_books,
                'total_quotes': total_quotes
            }
        })
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
        "message": "Application déployée avec succès (version complète avec administration)",
        "version": "2.0",
        "features": ["books", "quotes", "users", "admin"]
    })

# Point d'entrée pour le déploiement
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

