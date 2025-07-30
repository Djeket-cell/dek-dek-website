import os
import sys
import json
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import sqlite3

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configuration des uploads - Utiliser un dossier persistant pour Render
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'webm'}

# Créer les dossiers nécessaires
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'books'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

# Initialisation de la base de données
db = SQLAlchemy()

# ==================== MODÈLES DE BASE DE DONNÉES ====================

# Modèle User (Admin)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Modèle PublicUser (Utilisateurs publics pour commentaires)
class PublicUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hasher le mot de passe"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'comments_count': len(self.comments),
            'ratings_count': len(self.ratings)
        }

# Modèle Comment
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'book' ou 'quote'
    content_id = db.Column(db.Integer, nullable=False)  # ID du livre ou de la citation
    user_id = db.Column(db.Integer, db.ForeignKey('public_user.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)  # Modération
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'user_id': self.user_id,
            'username': self.author.username if self.author else 'Utilisateur supprimé',
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Modèle Rating (Notes/Évaluations)
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Note de 1 à 5
    content_type = db.Column(db.String(20), nullable=False)  # 'book' ou 'quote'
    content_id = db.Column(db.Integer, nullable=False)  # ID du livre ou de la citation
    user_id = db.Column(db.Integer, db.ForeignKey('public_user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contrainte d'unicité : un utilisateur ne peut noter qu'une fois le même contenu
    __table_args__ = (db.UniqueConstraint('user_id', 'content_type', 'content_id'),)

    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Utilisateur supprimé',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Modèle pour les médias uploadés
class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, video, document
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_featured = db.Column(db.Boolean, default=False)  # Pour afficher sur la page d'accueil
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'title': self.title,
            'description': self.description,
            'is_featured': self.is_featured,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'url': f'/static/uploads/{self.file_type}s/{self.filename}'
        }

# Configuration Flask avec chemins statiques corrigés pour Render
static_folder_path = os.path.join(BASE_DIR, 'static')
if not os.path.exists(static_folder_path):
    # Si le dossier static n'existe pas à la racine, essayer src/static
    static_folder_path = os.path.join(BASE_DIR, 'src', 'static')

app = Flask(__name__, 
           static_folder=static_folder_path,
           template_folder=os.path.join(BASE_DIR, 'templates'))

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app)

# Configuration de l'application
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialisation de la base de données
db.init_app(app)

def init_database():
    """Initialisation sécurisée de la base de données"""
    try:
        with app.app_context():
            # Supprimer et recréer toutes les tables pour éviter les problèmes de migration
            db.drop_all()
            db.create_all()
            
            # Créer un admin par défaut
            admin = User(username='admin', email='admin@dek-dek.com', is_admin=True)
            db.session.add(admin)
            
            # Créer quelques utilisateurs publics de test
            test_user1 = PublicUser(username='testuser1', email='test1@example.com')
            test_user1.set_password('password123')
            
            test_user2 = PublicUser(username='testuser2', email='test2@example.com')
            test_user2.set_password('password123')
            
            db.session.add(test_user1)
            db.session.add(test_user2)
            
            db.session.commit()
            print("Base de données initialisée avec succès")
            print("Utilisateurs de test créés: testuser1 et testuser2 (mot de passe: password123)")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")

# ==================== FONCTIONS UTILITAIRES ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Connexion requise'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def load_json_data(filename):
    """Charger les données JSON avec gestion d'erreur"""
    try:
        file_path = os.path.join(BASE_DIR, 'data', filename)
        if not os.path.exists(file_path):
            # Créer le fichier avec des données par défaut si il n'existe pas
            default_data = []
            if filename == 'books.json':
                default_data = [
                    {
                        "id": 1,
                        "title": "Guide du Développement Personnel",
                        "description": "Un livre complet pour développer votre potentiel et atteindre vos objectifs personnels et professionnels.",
                        "price": 19.99,
                        "image": "/static/uploads/images/default-book.jpg",
                        "category": "Développement personnel",
                        "author": "Expert Dek.Dek",
                        "pages": 250,
                        "format": "PDF",
                        "created_at": datetime.utcnow().isoformat()
                    },
                    {
                        "id": 2,
                        "title": "Maîtriser la Motivation",
                        "description": "Découvrez les secrets pour maintenir votre motivation au plus haut niveau et surmonter tous les obstacles.",
                        "price": 15.99,
                        "image": "/static/uploads/images/default-book2.jpg",
                        "category": "Motivation",
                        "author": "Coach Dek.Dek",
                        "pages": 180,
                        "format": "PDF",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
            elif filename == 'quotes.json':
                default_data = [
                    {
                        "id": 1,
                        "text": "Le succès n'est pas final, l'échec n'est pas fatal : c'est le courage de continuer qui compte.",
                        "author": "Winston Churchill",
                        "category": "Motivation",
                        "created_at": datetime.utcnow().isoformat()
                    },
                    {
                        "id": 2,
                        "text": "La seule façon de faire du bon travail est d'aimer ce que vous faites.",
                        "author": "Steve Jobs",
                        "category": "Travail",
                        "created_at": datetime.utcnow().isoformat()
                    },
                    {
                        "id": 3,
                        "text": "L'innovation distingue un leader d'un suiveur.",
                        "author": "Steve Jobs",
                        "category": "Leadership",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
            save_json_data(filename, default_data)
            return default_data
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de {filename}: {e}")
        return []

def save_json_data(filename, data):
    """Sauvegarder les données JSON"""
    try:
        file_path = os.path.join(BASE_DIR, 'data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de {filename}: {e}")
        return False

def get_content_stats(content_type, content_id):
    """Obtenir les statistiques d'un contenu (commentaires et notes)"""
    try:
        # Compter les commentaires approuvés
        comments_count = Comment.query.filter_by(
            content_type=content_type, 
            content_id=content_id, 
            is_approved=True
        ).count()
        
        # Calculer la note moyenne
        ratings = Rating.query.filter_by(
            content_type=content_type, 
            content_id=content_id
        ).all()
        
        average_rating = 0
        ratings_count = len(ratings)
        if ratings_count > 0:
            average_rating = sum(r.rating for r in ratings) / ratings_count
        
        return {
            'comments_count': comments_count,
            'ratings_count': ratings_count,
            'average_rating': round(average_rating, 1)
        }
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
        return {
            'comments_count': 0,
            'ratings_count': 0,
            'average_rating': 0
        }

# ==================== ROUTES POUR FICHIERS STATIQUES ====================
@app.route('/images/<filename>')
def serve_image(filename):
    """Servir les images statiques"""
    try:
        # Essayer d'abord dans static/images
        static_images_path = os.path.join(app.static_folder, 'images')
        if os.path.exists(os.path.join(static_images_path, filename)):
            return send_from_directory(static_images_path, filename)
        
        # Sinon essayer dans static/uploads/images
        upload_images_path = os.path.join(app.static_folder, 'uploads', 'images')
        if os.path.exists(os.path.join(upload_images_path, filename)):
            return send_from_directory(upload_images_path, filename)
        
        return "Image non trouvée", 404
    except Exception as e:
        print(f"Erreur lors du service de l'image {filename}: {e}")
        return f"Erreur: {str(e)}", 500

@app.route('/css/<filename>')
def serve_css(filename):
    """Servir les fichiers CSS"""
    try:
        css_path = os.path.join(app.static_folder, 'css')
        return send_from_directory(css_path, filename)
    except Exception as e:
        return f"Erreur CSS: {str(e)}", 500

@app.route('/js/<filename>')
def serve_js(filename):
    """Servir les fichiers JavaScript"""
    try:
        js_path = os.path.join(app.static_folder, 'js')
        return send_from_directory(js_path, filename)
    except Exception as e:
        return f"Erreur JS: {str(e)}", 500

# ==================== ROUTES PUBLIQUES ====================
@app.route('/')
def index():
    """Page d'accueil avec médias en vedette"""
    try:
        return render_template('public/index.html')
    except:
        # Fallback vers le fichier statique
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/livres')
def books_page():
    """Page dédiée aux livres"""
    try:
        return render_template('public/books.html')
    except:
        return "Page des livres en construction", 404

@app.route('/citations')
def quotes_page():
    """Page dédiée aux citations"""
    try:
        return render_template('public/quotes.html')
    except:
        return "Page des citations en construction", 404

@app.route('/contact')
def contact_page():
    """Page de contact"""
    try:
        return render_template('public/contact.html')
    except:
        return "Page de contact en construction", 404

@app.route('/login')
def login_page():
    """Page de connexion utilisateur"""
    try:
        return render_template('public/login.html')
    except:
        return "Page de connexion en construction", 404

@app.route('/register')
def register_page():
    """Page d'inscription utilisateur"""
    try:
        return render_template('public/register.html')
    except:
        return "Page d'inscription en construction", 404

# ==================== API PUBLIQUE ====================
@app.route('/api/featured-media')
def get_featured_media():
    """API pour récupérer les médias en vedette pour la page d'accueil"""
    try:
        featured_media = Media.query.filter_by(is_featured=True).order_by(Media.uploaded_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [media.to_dict() for media in featured_media],
            'count': len(featured_media)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/books')
def get_books():
    """API pour récupérer la liste des livres avec statistiques"""
    try:
        books = load_json_data('books.json')
        
        # Ajouter les statistiques à chaque livre
        for book in books:
            book_id = book.get('id')
            if book_id:
                stats = get_content_stats('book', book_id)
                book.update(stats)
        
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

@app.route('/api/books/<int:book_id>')
def get_book(book_id):
    """API pour récupérer un livre spécifique avec commentaires et notes"""
    try:
        books = load_json_data('books.json')
        book = next((b for b in books if b.get('id') == book_id), None)
        if not book:
            return jsonify({
                'success': False,
                'error': 'Livre non trouvé'
            }), 404
        
        # Ajouter les statistiques
        stats = get_content_stats('book', book_id)
        book.update(stats)
        
        # Ajouter les commentaires approuvés
        comments = Comment.query.filter_by(
            content_type='book', 
            content_id=book_id, 
            is_approved=True
        ).order_by(Comment.created_at.desc()).all()
        
        book['comments'] = [comment.to_dict() for comment in comments]
            
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
    """API pour récupérer la liste des citations avec statistiques"""
    try:
        quotes = load_json_data('quotes.json')
        
        # Ajouter les statistiques à chaque citation
        for quote in quotes:
            quote_id = quote.get('id')
            if quote_id:
                stats = get_content_stats('quote', quote_id)
                quote.update(stats)
        
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

@app.route('/api/quotes/<int:quote_id>')
def get_quote(quote_id):
    """API pour récupérer une citation spécifique avec commentaires"""
    try:
        quotes = load_json_data('quotes.json')
        quote = next((q for q in quotes if q.get('id') == quote_id), None)
        if not quote:
            return jsonify({
                'success': False,
                'error': 'Citation non trouvée'
            }), 404
        
        # Ajouter les statistiques
        stats = get_content_stats('quote', quote_id)
        quote.update(stats)
        
        # Ajouter les commentaires approuvés
        comments = Comment.query.filter_by(
            content_type='quote', 
            content_id=quote_id, 
            is_approved=True
        ).order_by(Comment.created_at.desc()).all()
        
        quote['comments'] = [comment.to_dict() for comment in comments]
            
        return jsonify({
            'success': True,
            'data': quote
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API AUTHENTIFICATION UTILISATEURS PUBLICS ====================
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Inscription d'un nouvel utilisateur public"""
    try:
        data = request.json
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({
                'success': False,
                'error': 'Username, email et password requis'
            }), 400
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = PublicUser.query.filter(
            (PublicUser.username == data['username']) | (PublicUser.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Nom d\'utilisateur ou email déjà utilisé'
            }), 409
        
        # Créer le nouvel utilisateur
        user = PublicUser(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Connecter automatiquement l'utilisateur
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'Inscription réussie'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Connexion d'un utilisateur public"""
    try:
        data = request.json
        if not data or not all(k in data for k in ['username', 'password']):
            return jsonify({
                'success': False,
                'error': 'Username et password requis'
            }), 400
        
        # Chercher l'utilisateur
        user = PublicUser.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'error': 'Identifiants incorrects'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Compte désactivé'
            }), 403
        
        # Connecter l'utilisateur
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'Connexion réussie'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """Déconnexion d'un utilisateur public"""
    try:
        session.pop('user_id', None)
        session.pop('username', None)
        
        return jsonify({
            'success': True,
            'message': 'Déconnexion réussie'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/me')
def get_current_user():
    """Obtenir les informations de l'utilisateur connecté"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Non connecté'
            }), 401
        
        user = PublicUser.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            session.pop('username', None)
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

# ==================== API COMMENTAIRES ====================
@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    """Ajouter un commentaire"""
    try:
        data = request.json
        if not data or not all(k in data for k in ['content', 'content_type', 'content_id']):
            return jsonify({
                'success': False,
                'error': 'Content, content_type et content_id requis'
            }), 400
        
        if data['content_type'] not in ['book', 'quote']:
            return jsonify({
                'success': False,
                'error': 'content_type doit être "book" ou "quote"'
            }), 400
        
        # Vérifier que le contenu existe
        if data['content_type'] == 'book':
            books = load_json_data('books.json')
            if not any(b.get('id') == data['content_id'] for b in books):
                return jsonify({
                    'success': False,
                    'error': 'Livre non trouvé'
                }), 404
        else:  # quote
            quotes = load_json_data('quotes.json')
            if not any(q.get('id') == data['content_id'] for q in quotes):
                return jsonify({
                    'success': False,
                    'error': 'Citation non trouvée'
                }), 404
        
        # Créer le commentaire
        comment = Comment(
            content=data['content'].strip(),
            content_type=data['content_type'],
            content_id=data['content_id'],
            user_id=session['user_id'],
            is_approved=False  # Nécessite une modération
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': comment.to_dict(),
            'message': 'Commentaire ajouté (en attente de modération)'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/comments/<content_type>/<int:content_id>')
def get_comments(content_type, content_id):
    """Récupérer les commentaires approuvés d'un contenu"""
    try:
        if content_type not in ['book', 'quote']:
            return jsonify({
                'success': False,
                'error': 'content_type doit être "book" ou "quote"'
            }), 400
        
        comments = Comment.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            is_approved=True
        ).order_by(Comment.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [comment.to_dict() for comment in comments],
            'count': len(comments)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API NOTES/ÉVALUATIONS ====================
@app.route('/api/ratings', methods=['POST'])
@login_required
def add_rating():
    """Ajouter ou modifier une note"""
    try:
        data = request.json
        if not data or not all(k in data for k in ['rating', 'content_type', 'content_id']):
            return jsonify({
                'success': False,
                'error': 'Rating, content_type et content_id requis'
            }), 400
        
        if not (1 <= data['rating'] <= 5):
            return jsonify({
                'success': False,
                'error': 'La note doit être entre 1 et 5'
            }), 400
        
        if data['content_type'] not in ['book', 'quote']:
            return jsonify({
                'success': False,
                'error': 'content_type doit être "book" ou "quote"'
            }), 400
        
        # Vérifier si l'utilisateur a déjà noté ce contenu
        existing_rating = Rating.query.filter_by(
            user_id=session['user_id'],
            content_type=data['content_type'],
            content_id=data['content_id']
        ).first()
        
        if existing_rating:
            # Mettre à jour la note existante
            existing_rating.rating = data['rating']
            message = 'Note mise à jour'
        else:
            # Créer une nouvelle note
            existing_rating = Rating(
                rating=data['rating'],
                content_type=data['content_type'],
                content_id=data['content_id'],
                user_id=session['user_id']
            )
            db.session.add(existing_rating)
            message = 'Note ajoutée'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': existing_rating.to_dict(),
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ratings/<content_type>/<int:content_id>')
def get_ratings(content_type, content_id):
    """Récupérer les statistiques de notes d'un contenu"""
    try:
        if content_type not in ['book', 'quote']:
            return jsonify({
                'success': False,
                'error': 'content_type doit être "book" ou "quote"'
            }), 400
        
        stats = get_content_stats(content_type, content_id)
        
        # Ajouter la distribution des notes
        ratings = Rating.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).all()
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            distribution[rating.rating] += 1
        
        return jsonify({
            'success': True,
            'data': {
                **stats,
                'distribution': distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ROUTES ADMINISTRATION ====================
@app.route('/admin')
def admin_login():
    """Page de connexion admin"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Traitement de la connexion admin"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Authentification simple (à améliorer en production)
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Connexion réussie!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects!', 'error')
            return redirect(url_for('admin_login'))
    except Exception as e:
        flash(f'Erreur de connexion: {str(e)}', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Déconnexion réussie!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Tableau de bord admin"""
    return render_template('admin/dashboard.html')

@app.route('/admin/books')
@admin_required
def admin_books():
    """Gestion des livres"""
    return render_template('admin/books.html')

@app.route('/admin/quotes')
@admin_required
def admin_quotes():
    """Gestion des citations"""
    return render_template('admin/quotes.html')

@app.route('/admin/media')
@admin_required
def admin_media():
    """Gestion des médias"""
    return render_template('admin/media.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    """Gestion des utilisateurs"""
    return render_template('admin/users.html')

@app.route('/admin/comments')
@admin_required
def admin_comments():
    """Gestion des commentaires"""
    return render_template('admin/comments.html')

# ==================== API ADMINISTRATION ====================
@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    """Statistiques pour l'administration"""
    try:
        total_users = User.query.count()
        admin_users = User.query.filter_by(is_admin=True).count()
        total_media = Media.query.count()
        featured_media = Media.query.filter_by(is_featured=True).count()
        
        # Statistiques des utilisateurs publics
        total_public_users = PublicUser.query.count()
        active_public_users = PublicUser.query.filter_by(is_active=True).count()
        
        # Statistiques des commentaires
        total_comments = Comment.query.count()
        pending_comments = Comment.query.filter_by(is_approved=False).count()
        approved_comments = Comment.query.filter_by(is_approved=True).count()
        
        # Statistiques des notes
        total_ratings = Rating.query.count()
        
        books = load_json_data('books.json')
        quotes = load_json_data('quotes.json')
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'admin_users': admin_users,
                'regular_users': total_users - admin_users,
                'total_public_users': total_public_users,
                'active_public_users': active_public_users,
                'total_books': len(books),
                'total_quotes': len(quotes),
                'total_media': total_media,
                'featured_media': featured_media,
                'total_comments': total_comments,
                'pending_comments': pending_comments,
                'approved_comments': approved_comments,
                'total_ratings': total_ratings
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API MODÉRATION COMMENTAIRES ====================
@app.route('/api/admin/comments')
@admin_required
def admin_get_comments():
    """Récupérer tous les commentaires pour modération"""
    try:
        status = request.args.get('status', 'all')  # all, pending, approved
        
        query = Comment.query
        if status == 'pending':
            query = query.filter_by(is_approved=False)
        elif status == 'approved':
            query = query.filter_by(is_approved=True)
        
        comments = query.order_by(Comment.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [comment.to_dict() for comment in comments],
            'count': len(comments)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/comments/<int:comment_id>/approve', methods=['POST'])
@admin_required
def admin_approve_comment(comment_id):
    """Approuver un commentaire"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({
                'success': False,
                'error': 'Commentaire non trouvé'
            }), 404
        
        comment.is_approved = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': comment.to_dict(),
            'message': 'Commentaire approuvé'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/comments/<int:comment_id>/reject', methods=['POST'])
@admin_required
def admin_reject_comment(comment_id):
    """Rejeter un commentaire"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({
                'success': False,
                'error': 'Commentaire non trouvé'
            }), 404
        
        comment.is_approved = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': comment.to_dict(),
            'message': 'Commentaire rejeté'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/comments/<int:comment_id>', methods=['DELETE'])
@admin_required
def admin_delete_comment(comment_id):
    """Supprimer un commentaire"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({
                'success': False,
                'error': 'Commentaire non trouvé'
            }), 404
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Commentaire supprimé'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION UTILISATEURS PUBLICS (ADMIN) ====================
@app.route('/api/admin/public-users')
@admin_required
def admin_get_public_users():
    """Récupérer tous les utilisateurs publics"""
    try:
        users = PublicUser.query.order_by(PublicUser.created_at.desc()).all()
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

@app.route('/api/admin/public-users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    """Activer/désactiver un utilisateur public"""
    try:
        user = PublicUser.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activé' if user.is_active else 'désactivé'
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': f'Utilisateur {status}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION MÉDIAS (INCHANGÉE) ====================
@app.route('/api/admin/media', methods=['GET'])
@admin_required
def admin_get_media():
    """Récupérer tous les médias"""
    try:
        media_list = Media.query.order_by(Media.uploaded_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [media.to_dict() for media in media_list],
            'count': len(media_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/media/upload', methods=['POST'])
@admin_required
def admin_upload_media():
    """Upload de fichiers média"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier sélectionné'
            }), 400
        
        file = request.files['file']
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        is_featured = request.form.get('is_featured') == 'true'
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Aucun fichier sélectionné'
            }), 400
        
        if file and allowed_file(file.filename):
            # Sécuriser le nom de fichier
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            
            # Générer un nom unique
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Déterminer le type de fichier
            if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                file_type = 'image'
                subfolder = 'images'
            elif file_extension in ['mp4', 'avi', 'mov', 'webm']:
                file_type = 'video'
                subfolder = 'videos'
            else:
                file_type = 'document'
                subfolder = 'books'
            
            # Chemin de sauvegarde dans static/uploads
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, unique_filename)
            
            # Sauvegarder le fichier
            file.save(file_path)
            
            # Enregistrer en base de données
            media = Media(
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_type,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                title=title,
                description=description,
                is_featured=is_featured
            )
            
            db.session.add(media)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': media.to_dict(),
                'message': 'Fichier uploadé avec succès'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Type de fichier non autorisé'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/media/<int:media_id>', methods=['PUT'])
@admin_required
def admin_update_media(media_id):
    """Mettre à jour un média"""
    try:
        media = Media.query.get(media_id)
        if not media:
            return jsonify({
                'success': False,
                'error': 'Média non trouvé'
            }), 404
        
        data = request.json
        if data:
            media.title = data.get('title', media.title)
            media.description = data.get('description', media.description)
            media.is_featured = data.get('is_featured', media.is_featured)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': media.to_dict(),
            'message': 'Média mis à jour avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/media/<int:media_id>', methods=['DELETE'])
@admin_required
def admin_delete_media(media_id):
    """Supprimer un média"""
    try:
        media = Media.query.get(media_id)
        if not media:
            return jsonify({
                'success': False,
                'error': 'Média non trouvé'
            }), 404
        
        # Supprimer le fichier physique
        if os.path.exists(media.file_path):
            os.remove(media.file_path)
        
        # Supprimer de la base de données
        db.session.delete(media)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Média supprimé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION LIVRES (INCHANGÉE) ====================
@app.route('/api/admin/books', methods=['POST'])
@admin_required
def admin_add_book():
    """Ajouter un livre"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
            
        books = load_json_data('books.json')
        
        # Générer un nouvel ID
        new_id = max([book.get('id', 0) for book in books], default=0) + 1
        
        new_book = {
            'id': new_id,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'price': float(data.get('price', 0)),
            'image': data.get('image', ''),
            'category': data.get('category', ''),
            'author': data.get('author', ''),
            'pages': int(data.get('pages', 0)),
            'format': data.get('format', 'PDF'),
            'created_at': datetime.utcnow().isoformat()
        }
        
        books.append(new_book)
        
        if save_json_data('books.json', books):
            return jsonify({
                'success': True,
                'data': new_book,
                'message': 'Livre ajouté avec succès'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/books/<int:book_id>', methods=['PUT'])
@admin_required
def admin_update_book(book_id):
    """Modifier un livre"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
            
        books = load_json_data('books.json')
        
        book_index = next((i for i, book in enumerate(books) if book.get('id') == book_id), None)
        if book_index is None:
            return jsonify({
                'success': False,
                'error': 'Livre non trouvé'
            }), 404
        
        # Mettre à jour le livre
        books[book_index].update({
            'title': data.get('title', books[book_index].get('title')),
            'description': data.get('description', books[book_index].get('description')),
            'price': float(data.get('price', books[book_index].get('price', 0))),
            'image': data.get('image', books[book_index].get('image')),
            'category': data.get('category', books[book_index].get('category')),
            'author': data.get('author', books[book_index].get('author')),
            'pages': int(data.get('pages', books[book_index].get('pages', 0))),
            'format': data.get('format', books[book_index].get('format')),
            'updated_at': datetime.utcnow().isoformat()
        })
        
        if save_json_data('books.json', books):
            return jsonify({
                'success': True,
                'data': books[book_index],
                'message': 'Livre modifié avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/books/<int:book_id>', methods=['DELETE'])
@admin_required
def admin_delete_book(book_id):
    """Supprimer un livre"""
    try:
        books = load_json_data('books.json')
        
        book_index = next((i for i, book in enumerate(books) if book.get('id') == book_id), None)
        if book_index is None:
            return jsonify({
                'success': False,
                'error': 'Livre non trouvé'
            }), 404
        
        deleted_book = books.pop(book_index)
        
        if save_json_data('books.json', books):
            return jsonify({
                'success': True,
                'message': 'Livre supprimé avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION CITATIONS (INCHANGÉE) ====================
@app.route('/api/admin/quotes', methods=['POST'])
@admin_required
def admin_add_quote():
    """Ajouter une citation"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
            
        quotes = load_json_data('quotes.json')
        
        # Générer un nouvel ID
        new_id = max([quote.get('id', 0) for quote in quotes], default=0) + 1
        
        new_quote = {
            'id': new_id,
            'text': data.get('text', ''),
            'author': data.get('author', ''),
            'category': data.get('category', ''),
            'created_at': datetime.utcnow().isoformat()
        }
        
        quotes.append(new_quote)
        
        if save_json_data('quotes.json', quotes):
            return jsonify({
                'success': True,
                'data': new_quote,
                'message': 'Citation ajoutée avec succès'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/quotes/<int:quote_id>', methods=['PUT'])
@admin_required
def admin_update_quote(quote_id):
    """Modifier une citation"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données manquantes'
            }), 400
            
        quotes = load_json_data('quotes.json')
        
        quote_index = next((i for i, quote in enumerate(quotes) if quote.get('id') == quote_id), None)
        if quote_index is None:
            return jsonify({
                'success': False,
                'error': 'Citation non trouvée'
            }), 404
        
        # Mettre à jour la citation
        quotes[quote_index].update({
            'text': data.get('text', quotes[quote_index].get('text')),
            'author': data.get('author', quotes[quote_index].get('author')),
            'category': data.get('category', quotes[quote_index].get('category')),
            'updated_at': datetime.utcnow().isoformat()
        })
        
        if save_json_data('quotes.json', quotes):
            return jsonify({
                'success': True,
                'data': quotes[quote_index],
                'message': 'Citation modifiée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/quotes/<int:quote_id>', methods=['DELETE'])
@admin_required
def admin_delete_quote(quote_id):
    """Supprimer une citation"""
    try:
        quotes = load_json_data('quotes.json')
        
        quote_index = next((i for i, quote in enumerate(quotes) if quote.get('id') == quote_id), None)
        if quote_index is None:
            return jsonify({
                'success': False,
                'error': 'Citation non trouvée'
            }), 404
        
        deleted_quote = quotes.pop(quote_index)
        
        if save_json_data('quotes.json', quotes):
            return jsonify({
                'success': True,
                'message': 'Citation supprimée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION UTILISATEURS ADMIN (INCHANGÉE) ====================
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    """Récupérer tous les utilisateurs admin"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
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

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def admin_create_user():
    """Créer un nouvel utilisateur admin"""
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

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Supprimer un utilisateur admin"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
        
        # Empêcher la suppression de l'admin principal
        if user.username == 'admin':
            return jsonify({
                'success': False,
                'error': 'Impossible de supprimer l\'administrateur principal'
            }), 403
        
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

@app.route('/health')
def health():
    """Route de santé pour vérifier que l'application fonctionne"""
    return jsonify({
        "status": "OK", 
        "message": "Application déployée avec succès (version finale avec commentaires)",
        "version": "6.0",
        "static_folder": app.static_folder,
        "features": [
            "books_with_prices", 
            "quotes", 
            "users", 
            "admin", 
            "media_upload", 
            "video_support", 
            "separate_pages", 
            "persistent_data", 
            "professional_ui", 
            "animations", 
            "responsive_design",
            "user_comments",
            "user_ratings",
            "comment_moderation",
            "public_user_auth",
            "notifications"
        ]
    })

# Initialisation de la base de données au démarrage
init_database()

# Point d'entrée pour le déploiement
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

