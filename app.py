from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  
    return conn

def create_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL
        )
    ''')
    conn.commit()
    conn.close()

# Function to calculate macros
def calculate_macros(user):
    weight = user['weight']
    height = user['height']
    age = user['age']
    gender = user['gender']

    if gender == "Vīrietis":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    daily_calories = bmr * 1.2  # Light activity multiplier

    protein = weight * 2  # 2g per kg
    fat = weight * 1      # 1g per kg

    protein_calories = protein * 4
    fat_calories = fat * 9

    remaining_calories = daily_calories - (protein_calories + fat_calories)
    carbs = remaining_calories / 4

    return round(daily_calories), round(carbs), round(protein), round(fat)

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if user:
        calories, carbs, protein, fat = calculate_macros(user)
        return render_template('home.html', calories=calories, carbs=carbs, protein=protein, fat=fat)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        return "Nepareizs lietotājvārds vai parole"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        height = request.form['height']
        weight = request.form['weight']

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, password, age, gender, height, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password, age, gender, height, weight))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Lietotājvārds jau eksistē"
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        age = request.form['age']
        gender = request.form['gender']
        height = request.form['height']
        weight = request.form['weight']

        conn.execute('''
            UPDATE users
            SET age = ?, gender = ?, height = ?, weight = ?
            WHERE id = ?
        ''', (age, gender, height, weight, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    conn.close()
    return render_template('edit_profile.html', user=user)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
