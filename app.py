from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'gymsecret'  # Needed for flash messages

def generate_unique_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    while True:
        athlete_id = random.randint(1000, 9999)
        c.execute("SELECT 1 FROM athletes WHERE id = ?", (athlete_id,))
        if not c.fetchone():
            conn.close()
            return athlete_id

def log_activity(action, details, athlete_id=None):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO activity_log (timestamp, action, details, athlete_id) VALUES (?, ?, ?, ?)",
              (timestamp, action, details, athlete_id))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Athletes table
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
    
    # Activity log table
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  action TEXT NOT NULL,
                  details TEXT NOT NULL,
                  athlete_id INTEGER,
                  FOREIGN KEY(athlete_id) REFERENCES athletes(id))''')
    
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
        
        # Log the registration activity
        log_activity(
            action="REGISTRATION",
            details=f"Registered new athlete: {first_name} {last_name} (ID: {athlete_id}) for {days} days",
            athlete_id=athlete_id
        )
        
        flash('Athlete registered successfully!', 'success')
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

@app.route('/history')
def history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all activities, newest first
    c.execute('''SELECT activity_log.*, athletes.first_name, athletes.last_name
                 FROM activity_log
                 LEFT JOIN athletes ON activity_log.athlete_id = athletes.id
                 ORDER BY timestamp DESC''')
    activities = c.fetchall()
    conn.close()
    
    # Format activities for display
    formatted_activities = []
    for activity in activities:
        formatted_activities.append({
            'id': activity[0],
            'timestamp': activity[1],
            'action': activity[2],
            'details': activity[3],
            'athlete_id': activity[4],
            'athlete_name': f"{activity[5]} {activity[6]}" if activity[5] and activity[6] else "N/A"
        })
    
    return render_template('history.html', activities=formatted_activities)

if __name__ == '__main__':
    app.run(debug=True)