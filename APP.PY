
# from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash
# import joblib
# import os

# # Load model and vectorizer
# model = joblib.load('logistic_regression_model.pkl')
# vectorizer = joblib.load('vectorizer.pkl')  # Make sure this file exists too

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# db = SQLAlchemy(app)

# # User model
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True, nullable=False)
#     password = db.Column(db.String(100), nullable=False)

# # Homepage
# @app.route('/')
# def index():
#     return render_template('index.html')

# # Dashboard
# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     sentiment_result = None
#     if request.method == 'POST':
#         text = request.form.get('text')
#         if text:
#             vectorized = vectorizer.transform([text])
#             prediction = model.predict(vectorized)[0]
#             sentiment_result = {1: "Positive", 0: "Neutral", -1: "Negative"}.get(prediction, "Unknown")

#     return render_template('dashboard.html', username=session['username'], sentiment=sentiment_result)

# # Sentiment prediction route
# @app.route('/predict', methods=['POST'])
# def predict():
#     data = request.json
#     if 'text' not in data:
#         return jsonify({'error': 'No text provided'}), 400

#     text = [data['text']]
#     text_vectorized = vectorizer.transform(text)
#     prediction = model.predict(text_vectorized)[0]

#     sentiment_map = {1: "Positive", 0: "Neutral", -1: "Negative"}
#     sentiment = sentiment_map.get(prediction, "Unknown")

#     # Track sentiments per session
#     if 'sentiment_counts' not in session:
#         session['sentiment_counts'] = {'Positive': 0, 'Negative': 0, 'Neutral': 0}

#     if sentiment in session['sentiment_counts']:
#         session['sentiment_counts'][sentiment] += 1
#     else:
#         session['sentiment_counts'][sentiment] = 1

#     session.modified = True

#     return jsonify({'text': data['text'], 'sentiment': sentiment})

# # Sentiment chart data route
# @app.route('/sentiment_stats')
# def sentiment_stats():
#     default_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
#     return jsonify(session.get('sentiment_counts', default_counts))

# # About page
# @app.route('/about')
# def about():
#     return render_template('about.html')

# # Contact page
# @app.route('/contact')
# def contact():
#     return render_template('contact.html')

# # Login route
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(username=username).first()
#         if user and check_password_hash(user.password, password):
#             session['username'] = username
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid credentials', 'danger')
#     return render_template('login.html')

# # Register route
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         confirm_password = request.form.get('confirm_password')

#         if password != confirm_password:
#             flash('Passwords do not match', 'danger')
#             return redirect(url_for('register'))

#         hashed_password = generate_password_hash(password)
#         new_user = User(username=username, password=hashed_password)
#         db.session.add(new_user)
#         db.session.commit()

#         flash('Registration successful! You can now log in.', 'success')
#         return redirect(url_for('login'))

#     return render_template('register.html')

# # Logout route
# @app.route('/logout')
# def logout():
#     session.pop('username', None)
#     return redirect(url_for('index'))

# # Create tables and run app
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from Model import db, User  # Import from model.py
import joblib

# Load ML model and vectorizer
model = joblib.load('logistic_regression_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db.init_app(app)

# Redirect root to login
@app.route('/')
def root():
    return redirect(url_for('login'))

# Index (optional public homepage)
@app.route('/index')
def index():
    return render_template('index.html')

# Dashboard (Protected sentiment analysis home)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    sentiment_result = None
    if request.method == 'POST':
        text = request.form.get('text')
        if text:
            vectorized = vectorizer.transform([text])
            prediction = model.predict(vectorized)[0]
            sentiment_result = {1: "Positive", 0: "Neutral", -1: "Negative"}.get(prediction, "Unknown")

    return render_template('dashboard.html', username=session['username'], sentiment=sentiment_result)

# Predict sentiment via API
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = [data['text']]
    text_vectorized = vectorizer.transform(text)
    prediction = model.predict(text_vectorized)[0]

    sentiment_map = {1: "Positive", 0: "Neutral", -1: "Negative"}
    sentiment = sentiment_map.get(prediction, "Unknown")

    # Track sentiment count in session
    if 'sentiment_counts' not in session:
        session['sentiment_counts'] = {'Positive': 0, 'Negative': 0, 'Neutral': 0}

    session['sentiment_counts'][sentiment] = session['sentiment_counts'].get(sentiment, 0) + 1
    session.modified = True

    return jsonify({'text': data['text'], 'sentiment': sentiment})

# Sentiment chart stats
@app.route('/sentiment_stats')
def sentiment_stats():
    default_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    return jsonify(session.get('sentiment_counts', default_counts))

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
