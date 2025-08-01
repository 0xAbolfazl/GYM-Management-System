from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS athletes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  full_name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  registration_date TEXT NOT NULL,
                  days_remaining INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        days = int(request.form['days'])
        
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO athletes (full_name, phone, registration_date, days_remaining) VALUES (?, ?, ?, ?)",
                  (full_name, phone, registration_date, days))
        conn.commit()
        conn.close()
        
        return redirect(url_for('athletes'))
    
    return render_template('register.html')

@app.route('/athletes')
def athletes():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM athletes ORDER BY registration_date DESC")
    athletes_data = c.fetchall()
    conn.close()
    
    # Calculate remaining days for each athlete
    athletes = []
    for athlete in athletes_data:
        reg_date = datetime.strptime(athlete[3], '%Y-%m-%d %H:%M:%S')
        end_date = reg_date + timedelta(days=athlete[4])
        remaining_days = (end_date - datetime.now()).days
        remaining_days = max(0, remaining_days)  # Don't show negative days
        
        athlete_dict = {
            'id': athlete[0],
            'full_name': athlete[1],
            'phone': athlete[2],
            'registration_date': reg_date.strftime('%Y-%m-%d'),
            'days_remaining': remaining_days,
            'original_days': athlete[4]
        }
        athletes.append(athlete_dict)
    
    return render_template('athletes.html', athletes=athletes)

if __name__ == '__main__':
    app.run(debug=True)