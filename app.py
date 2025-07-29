import os
import sys
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configuration des uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'webm'}

# Créer le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'books'), exist_ok=True)

# Initialisation de la base de données
db = SQLAlchemy()

# Modèle User
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
            'url': f'/uploads/{self.file_type}s/{self.filename}'
        }

app = Flask(__name__, 
           static_folder=os.path.join(BASE_DIR, 'src', 'static'),
           template_folder=os.path.join(BASE_DIR, 'templates'))

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app)

# Configuration de l'application
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Créer le dossier de base de données s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'src', 'database'), exist_ok=True)

# Initialisation de la base de données
db.init_app(app)

def migrate_database():
    """Migration de la base de données pour ajouter les colonnes manquantes"""
    try:
        # Vérifier si la colonne is_admin existe
        with app.app_context():
            result = db.engine.execute("PRAGMA table_info(user)")
            columns = [row[1] for row in result]
            
            if 'is_admin' not in columns:
                print("Migration: Ajout de la colonne is_admin à la table user")
                db.engine.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                
            if 'created_at' not in columns:
                print("Migration: Ajout de la colonne created_at à la table user")
                db.engine.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
                
        print("Migration de la base de données terminée avec succès")
        return True
    except Exception as e:
        print(f"Erreur lors de la migration: {e}")
        # Si la migration échoue, on supprime et recrée la base
        try:
            db_path = os.path.join(BASE_DIR, 'src', 'database', 'app.db')
            if os.path.exists(db_path):
                os.remove(db_path)
                print("Ancienne base de données supprimée, création d'une nouvelle base")
            return False
        except Exception as e2:
            print(f"Erreur lors de la suppression de l'ancienne base: {e2}")
            return False

# Création des tables avec migration
with app.app_context():
    try:
        # Essayer de migrer d'abord
        migration_success = migrate_database()
        
        if not migration_success:
            # Si la migration échoue, créer toutes les tables
            db.create_all()
            print("Nouvelles tables créées")
        
        # Créer un admin par défaut s'il n'existe pas
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@dek-dek.com', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Utilisateur admin créé")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        # En dernier recours, supprimer et recréer
        try:
            db_path = os.path.join(BASE_DIR, 'src', 'database', 'app.db')
            if os.path.exists(db_path):
                os.remove(db_path)
            db.create_all()
            admin = User(username='admin', email='admin@dek-dek.com', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Base de données recréée avec succès")
        except Exception as e2:
            print(f"Erreur critique lors de la création de la base: {e2}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_json_data(filename):
    """Charger les données JSON avec gestion d'erreur"""
    try:
        file_path = os.path.join(BASE_DIR, 'data', filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
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
    """API pour récupérer la liste des livres"""
    try:
        books = load_json_data('books.json')
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
    """API pour récupérer un livre spécifique"""
    try:
        books = load_json_data('books.json')
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
        quotes = load_json_data('quotes.json')
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

# ==================== ROUTES UPLOADS ====================
@app.route('/uploads/<file_type>/<filename>')
def uploaded_file(file_type, filename):
    """Servir les fichiers uploadés"""
    try:
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file_type, filename)
        if os.path.exists(upload_path):
            return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], file_type), filename)
        else:
            return "Fichier non trouvé", 404
    except Exception as e:
        return f"Erreur: {str(e)}", 500

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
    """Tableau de bord admin - Gestion de la page d'accueil"""
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
        
        books = load_json_data('books.json')
        quotes = load_json_data('quotes.json')
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'admin_users': admin_users,
                'regular_users': total_users - admin_users,
                'total_books': len(books),
                'total_quotes': len(quotes),
                'total_media': total_media,
                'featured_media': featured_media
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API GESTION MÉDIAS ====================
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
            
            # Chemin de sauvegarde
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

# ==================== API GESTION LIVRES ====================
@app.route('/api/admin/books', methods=['POST'])
@admin_required
def admin_add_book():
    """Ajouter un livre"""
    try:
        data = request.json
        books = load_json_data('books.json')
        
        # Générer un nouvel ID
        new_id = max([book.get('id', 0) for book in books], default=0) + 1
        
        new_book = {
            'id': new_id,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'price': data.get('price', 0),
            'image': data.get('image', ''),
            'category': data.get('category', ''),
            'author': data.get('author', ''),
            'pages': data.get('pages', 0),
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
            'price': data.get('price', books[book_index].get('price')),
            'image': data.get('image', books[book_index].get('image')),
            'category': data.get('category', books[book_index].get('category')),
            'author': data.get('author', books[book_index].get('author')),
            'pages': data.get('pages', books[book_index].get('pages')),
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

# ==================== API GESTION CITATIONS ====================
@app.route('/api/admin/quotes', methods=['POST'])
@admin_required
def admin_add_quote():
    """Ajouter une citation"""
    try:
        data = request.json
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

# ==================== API GESTION UTILISATEURS ====================
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    """Récupérer tous les utilisateurs"""
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

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Supprimer un utilisateur"""
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
        "message": "Application déployée avec succès (version corrigée avec migration DB)",
        "version": "4.1",
        "features": ["books", "quotes", "users", "admin", "media_upload", "video_support", "separate_pages", "db_migration"]
    })

# Point d'entrée pour le déploiement
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


