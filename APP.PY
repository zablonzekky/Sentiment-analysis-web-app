from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from Model import db, User  # Import from model.py
import joblib
from datetime import datetime
from io import StringIO, BytesIO
import csv
import base64
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load ML model and vectorizer
model = joblib.load('logistic_regression_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db.init_app(app)

# New: Model for storing sentiment analysis history
class SentimentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
            # Save analysis to database history
            new_entry = SentimentHistory(text=text, sentiment=sentiment_result)
            db.session.add(new_entry)
            db.session.commit()

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

    # Save the analysis to database history
    new_entry = SentimentHistory(text=data['text'], sentiment=sentiment)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'text': data['text'], 'sentiment': sentiment})

# Sentiment chart stats (session-based)
@app.route('/sentiment_stats')
def sentiment_stats():
    default_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    return jsonify(session.get('sentiment_counts', default_counts))

@app.route('/download_results')
def download_results():
    history = SentimentHistory.query.order_by(SentimentHistory.timestamp.desc()).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Text', 'Sentiment', 'Timestamp'])
    for entry in history:
        writer.writerow([entry.text, entry.sentiment, entry.timestamp])
    # Convert the CSV text to bytes and create a BytesIO stream
    bytes_output = BytesIO(output.getvalue().encode('utf-8'))
    bytes_output.seek(0)
    return send_file(bytes_output, mimetype='text/csv', as_attachment=True, download_name='sentiment_results.csv')


# Generate Word Cloud from analyzed texts
@app.route('/generate_wordcloud')
def generate_wordcloud():
    history = SentimentHistory.query.all()
    texts = [entry.text for entry in history]
    combined_text = " ".join(texts) if texts else "No data available"
    wc = WordCloud(width=800, height=400, background_color='white').generate(combined_text)
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode()
    return render_template('wordcloud.html', img_data=img_data)

# History Log: Display past sentiment analysis activities
@app.route('/history')
def history():
    history_data = SentimentHistory.query.order_by(SentimentHistory.timestamp.desc()).all()
    return render_template('history.html', history=history_data)

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
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
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
