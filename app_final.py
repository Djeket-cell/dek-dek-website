from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__, template_folder='src/static', static_folder='src/static')

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        return "Hello! Your Flask app is running. Please check that index.html exists in src/static/"

@app.route('/api/books')
def get_books():
    try:
        with open('data/books.json', 'r') as f:
            books = json.load(f)
        return jsonify(books)
    except FileNotFoundError:
        return jsonify({"error": "books.json not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/quotes')
def get_quotes():
    try:
        with open('data/quotes.json', 'r') as f:
            quotes = json.load(f)
        return jsonify(quotes)
    except FileNotFoundError:
        return jsonify({"error": "quotes.json not found"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/health')
def health():
    return jsonify({"status": "OK", "message": "App is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

