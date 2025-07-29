from flask import Flask, render_template, jsonify
import json

app = Flask(__name__, template_folder='src/static', static_folder='src/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/books')
def get_books():
    with open('data/books.json', 'r') as f:
        books = json.load(f)
    return jsonify(books)

@app.route('/api/quotes')
def get_quotes():
    with open('data/quotes.json', 'r') as f:
        quotes = json.load(f)
    return jsonify(quotes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

