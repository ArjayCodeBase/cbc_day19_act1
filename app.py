from flask import Flask, render_template, request, redirect, session, url_for, g
from flask_session import Session
import sqlite3
import os
import datetime

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = '9f2b97a6c2f8e9bb2341dfd6bced5ff21e5a8cd0c3b8e7ea42f6a3cb9fce1cb9'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Database setup
DATABASE = os.path.join(app.root_path, 'app.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        fname TEXT, mname TEXT, lname TEXT,
        age INTEGER, address TEXT, bday TEXT,
        submitted_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    ''')
    db.commit()

# Wrap the init_db() call in app context
with app.app_context():
    init_db()

# Routes

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')
        cpw = request.form.get('confirm_password')

        if not email or not pw or pw != cpw:
            return "Invalid input", 400

        db = get_db()
        try:
            db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, pw))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already registered", 400

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, pw)).fetchone()

        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('home'))

        return "Login failed", 401

    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    rows = db.execute(
        'SELECT fname, mname, lname, age, address, bday, submitted_at '
        'FROM user_info WHERE user_id = ? ORDER BY submitted_at DESC',
        (session['user_id'],)
    ).fetchall()

    infos = [dict(row) for row in rows]
    return render_template(
        'home.html',
        email=session['user_email'],
        infos=infos
    )



@app.route('/add-info', methods=['GET', 'POST'])
def add_info():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = {
            'fname': request.form.get('fname'),
            'mname': request.form.get('mname'),
            'lname': request.form.get('lname'),
            'age': request.form.get('age'),
            'address': request.form.get('address'),
            'bday': request.form.get('bday'),
            'submitted_at': datetime.datetime.utcnow().isoformat()
        }

        db = get_db()
        db.execute(''' 
            INSERT INTO user_info (user_id, fname, mname, lname, age, address, bday, submitted_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], data['fname'], data['mname'], data['lname'],
            data['age'], data['address'], data['bday'], data['submitted_at']
        ))
        db.commit()

        return "Information submitted successfully.", 200

    return render_template('add_info.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))

