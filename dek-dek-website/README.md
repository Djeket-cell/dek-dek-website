# Dek.Dek - Site Web de Livres Numériques

## Description

Dek.Dek est un site web moderne pour la vente de livres numériques et le partage de citations inspirantes. Le site est développé avec Flask (Python) pour le backend et HTML/CSS/JavaScript pour le frontend.

## Fonctionnalités

- **Catalogue de livres numériques** : Présentation des livres avec descriptions, prix et boutons d'achat
- **Citations inspirantes** : Collection de citations motivantes
- **Intégration Wave** : Système de paiement via Wave (Côte d'Ivoire)
- **Design responsive** : Compatible mobile et desktop
- **API REST** : Endpoints pour les livres et citations

## Structure du Projet

```
dek-dek-website/
├── src/
│   ├── main.py              # Application Flask principale
│   ├── routes/              # Routes API
│   │   ├── books.py         # API des livres
│   │   ├── quotes.py        # API des citations
│   │   └── user.py          # API utilisateurs (template)
│   ├── models/              # Modèles de données
│   │   └── user.py          # Modèle utilisateur (template)
│   └── static/              # Fichiers statiques
│       ├── index.html       # Page principale
│       ├── css/style.css    # Styles CSS
│       ├── js/main.js       # JavaScript
│       └── images/logo.png  # Logo Dek.Dek
├── data/
│   ├── books.json           # Données des livres
│   └── quotes.json          # Données des citations
├── requirements.txt         # Dépendances Python
└── README.md               # Ce fichier
```

## Installation Locale

### Prérequis
- Python 3.8+
- Git

### Étapes

1. **Cloner le dépôt**
   ```bash
   git clone <URL_DU_DEPOT>
   cd dek-dek-website
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer l'application**
   ```bash
   python src/main.py
   ```

5. **Accéder au site**
   Ouvrez votre navigateur et allez à `http://localhost:5000`

## Déploiement sur Render

### Étape 1 : Préparer le Dépôt GitHub

1. **Créer un nouveau dépôt sur GitHub**
   - Allez sur [GitHub.com](https://github.com)
   - Cliquez sur "New repository"
   - Nommez-le `dek-dek-website`
   - Laissez-le public ou privé selon votre préférence
   - Ne cochez pas "Initialize with README" (nous avons déjà un README)

2. **Pousser le code vers GitHub**
   ```bash
   # Dans le dossier de votre projet
   git remote add origin https://github.com/VOTRE_USERNAME/dek-dek-website.git
   git branch -M main
   git push -u origin main
   ```

### Étape 2 : Déployer sur Render

1. **Créer un compte Render**
   - Allez sur [render.com](https://render.com)
   - Inscrivez-vous avec votre compte GitHub

2. **Créer un nouveau Web Service**
   - Dans le dashboard Render, cliquez sur "New +"
   - Sélectionnez "Web Service"
   - Connectez votre dépôt GitHub `dek-dek-website`

3. **Configuration du service**
   - **Name** : `dek-dek-website` (ou le nom de votre choix)
   - **Environment** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python src/main.py`
   - **Plan** : Sélectionnez "Free" pour commencer

4. **Variables d'environnement (optionnel)**
   Si vous avez des variables d'environnement, ajoutez-les dans la section "Environment Variables"

5. **Déployer**
   - Cliquez sur "Create Web Service"
   - Render va automatiquement déployer votre application
   - Le processus prend généralement 2-5 minutes

### Étape 3 : Accéder à votre Site

Une fois le déploiement terminé :
- Render vous fournira une URL (ex: `https://dek-dek-website.onrender.com`)
- Votre site sera accessible publiquement à cette adresse
- Les mises à jour automatiques se feront à chaque push sur la branche `main`

## Configuration du Paiement Wave

Le site est configuré pour utiliser Wave comme système de paiement :

1. **Lien de paiement** : Configuré dans `src/static/js/main.js`
   ```javascript
   const WAVE_PAYMENT_URL = 'https://pay.wave.com/m/M_ci_v2lk7iNUKi75/c/ci/';
   ```

2. **Processus d'achat** :
   - L'utilisateur clique sur "Acheter maintenant"
   - Une popup affiche les instructions de paiement
   - L'utilisateur est redirigé vers Wave
   - Il doit envoyer la preuve de paiement par WhatsApp
   - Vous validez manuellement et envoyez le livre par email

## Personnalisation

### Modifier les Livres
Éditez le fichier `data/books.json` pour ajouter/modifier les livres :
```json
{
  "id": 4,
  "title": "Nouveau Livre",
  "author": "Dek.Dek",
  "description": "Description du livre...",
  "price": 5000,
  "currency": "XOF",
  "category": "Catégorie",
  "pages": 100,
  "format": "PDF",
  "available": true
}
```

### Modifier les Citations
Éditez le fichier `data/quotes.json` pour ajouter/modifier les citations :
```json
{
  "id": 6,
  "text": "Votre nouvelle citation...",
  "author": "Auteur",
  "category": "Catégorie"
}
```

### Modifier le Design
- **CSS** : Éditez `src/static/css/style.css`
- **HTML** : Éditez `src/static/index.html`
- **JavaScript** : Éditez `src/static/js/main.js`

## API Endpoints

Le site expose plusieurs endpoints API :

- `GET /api/books` - Liste tous les livres
- `GET /api/books/<id>` - Détails d'un livre spécifique
- `GET /api/quotes` - Liste toutes les citations
- `GET /api/quotes/<id>` - Détails d'une citation spécifique
- `GET /api/quotes/random` - Citation aléatoire

## Support

Pour toute question ou problème :
- **WhatsApp** : +225 01 42 11 61 72
- **Email** : contact@dek-dek.com

## Licence

© 2025 Dek.Dek. Tous droits réservés.

---

**Note** : Ce projet utilise le plan gratuit de Render qui peut avoir des limitations (mise en veille après inactivité, bande passante limitée). Pour un usage professionnel intensif, considérez un plan payant.

