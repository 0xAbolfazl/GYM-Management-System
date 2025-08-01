from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS athletes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    (first_name, last_name, phone, emergency_phone, father_name, 
                     birth_date, registration_date, start_date, days_remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (first_name, last_name, phone, emergency_phone, father_name,
                   birth_date, registration_date, start_date, days))
        conn.commit()
        conn.close()
        
        return redirect(url_for('athletes'))
    
    default_start = datetime.now().strftime('%Y-%m-%d')
    return render_template('register.html', default_start=default_start)


@app.route('/athletes')
def athletes():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
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
    
    return render_template('athletes.html', athletes=athletes)

if __name__ == '__main__':
    app.run(debug=True)