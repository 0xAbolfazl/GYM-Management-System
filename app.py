from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import random

app = Flask(__name__)

def generate_unique_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    while True:
        # Generate a random 4-digit ID between 1000-9999
        athlete_id = random.randint(1000, 9999)
        
        # Check if ID already exists
        c.execute("SELECT 1 FROM athletes WHERE id = ?", (athlete_id,))
        if not c.fetchone():
            conn.close()
            return athlete_id

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS athletes
                 (id INTEGER PRIMARY KEY,
                  first_name TEXT NOT NULL,
                  last_name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  emergency_phone TEXT,
                  father_name TEXT,
                  birth_date TEXT,
                  registration_date TEXT NOT NULL,
                  start_date TEXT NOT NULL,
                  days_remaining INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get total athletes count
    c.execute("SELECT COUNT(*) FROM athletes")
    total_athletes = c.fetchone()[0]
    
    # Get active athletes (with days remaining > 0)
    c.execute("SELECT COUNT(*) FROM athletes WHERE days_remaining > 0")
    active_athletes = c.fetchone()[0]
    
    # Get expiring soon athletes (less than 7 days remaining)
    c.execute("SELECT COUNT(*) FROM athletes WHERE days_remaining > 0 AND days_remaining < 7")
    expiring_soon = c.fetchone()[0]
    
    # Get recent registrations (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute("SELECT COUNT(*) FROM athletes WHERE registration_date > ?", (seven_days_ago,))
    recent_registrations = c.fetchone()[0]
    
    conn.close()
    
    return render_template('home.html', 
                         total_athletes=total_athletes,
                         active_athletes=active_athletes,
                         expiring_soon=expiring_soon,
                         recent_registrations=recent_registrations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        athlete_id = generate_unique_id()
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        emergency_phone = request.form.get('emergency_phone')
        father_name = request.form.get('father_name')
        birth_date = request.form.get('birth_date')
        days = int(request.form['days'])
        start_date = request.form.get('start_date') or datetime.now().strftime('%Y-%m-%d')
        
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO athletes 
                    (id, first_name, last_name, phone, emergency_phone, father_name, 
                     birth_date, registration_date, start_date, days_remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (athlete_id, first_name, last_name, phone, emergency_phone, father_name,
                   birth_date, registration_date, start_date, days))
        conn.commit()
        conn.close()
        
        return redirect(url_for('athletes'))
    
    default_start = datetime.now().strftime('%Y-%m-%d')
    return render_template('register.html', default_start=default_start)

@app.route('/athletes')
def athletes():
    search_query = request.args.get('search', '').strip()
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if search_query:
        # Search by ID or name (first, last, or full name)
        query = """
        SELECT * FROM athletes 
        WHERE id = ? OR 
              first_name LIKE ? OR 
              last_name LIKE ? OR
              first_name || ' ' || last_name LIKE ?
        ORDER BY start_date DESC
        """
        search_param = f"%{search_query}%"
        c.execute(query, (search_query, search_param, search_param, search_param))
    else:
        # Get all athletes
        c.execute("SELECT * FROM athletes ORDER BY start_date DESC")
    
    athletes_data = c.fetchall()
    conn.close()
    
    athletes = []
    for athlete in athletes_data:
        start_date_str = athlete[8] if isinstance(athlete[8], str) else athlete[8].strftime('%Y-%m-%d')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        end_date = start_date + timedelta(days=athlete[9])
        remaining_days = (end_date - datetime.now()).days
        remaining_days = max(0, remaining_days)
        
        birth_date = athlete[6]
        if birth_date:
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            else:
                birth_date = birth_date.strftime('%Y-%m-%d')
        
        athlete_dict = {
            'id': athlete[0],
            'first_name': athlete[1],
            'last_name': athlete[2],
            'full_name': f"{athlete[1]} {athlete[2]}",
            'phone': athlete[3],
            'emergency_phone': athlete[4],
            'father_name': athlete[5],
            'birth_date': birth_date,
            'registration_date': athlete[7].strftime('%Y-%m-%d %H:%M:%S') if not isinstance(athlete[7], str) else athlete[7],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'days_remaining': remaining_days,
            'original_days': athlete[9]
        }
        athletes.append(athlete_dict)
    
    return render_template('athletes.html', athletes=athletes, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)