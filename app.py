from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import random
from functools import wraps

app = Flask(__name__)
app.secret_key = 'gymsecret'  # Change this to a secure secret key

# Database Helper Functions
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_unique_id():
    conn = get_db_connection()
    while True:
        athlete_id = random.randint(1000, 9999)
        athlete = conn.execute('SELECT 1 FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
        if not athlete:
            conn.close()
            return athlete_id

def log_activity(action, details, athlete_id=None):
    conn = get_db_connection()
    conn.execute('INSERT INTO activity_log (timestamp, action, details, athlete_id) VALUES (?, ?, ?, ?)',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), action, details, athlete_id))
    conn.commit()
    conn.close()

def init_db():
    conn = get_db_connection()
    
    # Athletes table
    conn.execute('''CREATE TABLE IF NOT EXISTS athletes
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
    conn.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  action TEXT NOT NULL,
                  details TEXT NOT NULL,
                  athlete_id INTEGER,
                  FOREIGN KEY(athlete_id) REFERENCES athletes(id))''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Routes
@app.route('/')
def home():
    conn = get_db_connection()
    
    stats = {
        'total_athletes': conn.execute('SELECT COUNT(*) FROM athletes').fetchone()[0],
        'active_athletes': conn.execute('SELECT COUNT(*) FROM athletes WHERE days_remaining > 0').fetchone()[0],
        'expiring_soon': conn.execute('SELECT COUNT(*) FROM athletes WHERE days_remaining > 0 AND days_remaining < 7').fetchone()[0],
        'recent_registrations': conn.execute(
            'SELECT COUNT(*) FROM athletes WHERE registration_date > ?',
            ((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),)
        ).fetchone()[0]
    }
    
    conn.close()
    return render_template('home.html', **stats)

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
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO athletes 
                      (id, first_name, last_name, phone, emergency_phone, father_name, 
                       birth_date, registration_date, start_date, days_remaining)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (athlete_id, first_name, last_name, phone, emergency_phone, father_name,
                     birth_date, registration_date, start_date, days))
        conn.commit()
        conn.close()
        
        log_activity(
            action="REGISTRATION",
            details=f"Registered new athlete: {first_name} {last_name} (ID: {athlete_id}) for {days} days",
            athlete_id=athlete_id
        )
        
        flash('Athlete registered successfully!', 'success')
        return redirect(url_for('athletes'))
    
    return render_template('register.html', default_start=datetime.now().strftime('%Y-%m-%d'))

@app.route('/athletes')
def athletes():
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    
    if search_query:
        query = '''SELECT * FROM athletes 
                 WHERE id = ? OR 
                       first_name LIKE ? OR 
                       last_name LIKE ? OR
                       first_name || ' ' || last_name LIKE ?
                 ORDER BY start_date DESC'''
        search_param = f"%{search_query}%"
        athletes_data = conn.execute(query, (search_query, search_param, search_param, search_param)).fetchall()
    else:
        athletes_data = conn.execute('SELECT * FROM athletes ORDER BY start_date DESC').fetchall()
    
    athletes = []
    for athlete in athletes_data:
        start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=athlete['days_remaining'])
        remaining_days = (end_date - datetime.now()).days
        remaining_days = max(0, remaining_days)
        
        athletes.append({
            'id': athlete['id'],
            'first_name': athlete['first_name'],
            'last_name': athlete['last_name'],
            'phone': athlete['phone'],
            'registration_date': athlete['registration_date'],
            'start_date': athlete['start_date'],
            'end_date': end_date.strftime('%Y-%m-%d'), 
            'days_remaining': remaining_days,
            'original_days': athlete['days_remaining']
        })
    
    conn.close()
    return render_template('athletes.html', 
                         athletes=athletes, 
                         search_query=search_query,
                         datetime=datetime,  
                         timedelta=timedelta) 

@app.route('/athlete/<int:athlete_id>')
def view_athlete(athlete_id):
    conn = get_db_connection()
    athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
    end_date = start_date + timedelta(days=athlete['days_remaining'])
    
    athlete_data = {
        'id': athlete['id'],
        'first_name': athlete['first_name'],
        'last_name': athlete['last_name'],
        'phone': athlete['phone'],
        'emergency_phone': athlete['emergency_phone'],
        'father_name': athlete['father_name'],
        'birth_date': athlete['birth_date'],
        'registration_date': athlete['registration_date'],
        'start_date': athlete['start_date'],
        'end_date': end_date.strftime('%Y-%m-%d'),  
        'days_remaining': (end_date - datetime.now()).days,
        'original_days': athlete['days_remaining']
    }
    
    return render_template('view_athlete.html', athlete=athlete_data)

@app.route('/athlete/<int:athlete_id>/edit', methods=['GET', 'POST'])
def edit_athlete(athlete_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        emergency_phone = request.form.get('emergency_phone')
        father_name = request.form.get('father_name')
        birth_date = request.form.get('birth_date')
        
        conn.execute('''UPDATE athletes SET
                      first_name = ?, last_name = ?, phone = ?,
                      emergency_phone = ?, father_name = ?, birth_date = ?
                      WHERE id = ?''',
                    (first_name, last_name, phone, emergency_phone, 
                     father_name, birth_date, athlete_id))
        conn.commit()
        conn.close()
        
        log_activity(
            action="UPDATE",
            details=f"Updated athlete details: {first_name} {last_name} (ID: {athlete_id})",
            athlete_id=athlete_id
        )
        
        flash('Athlete updated successfully!', 'success')
        return redirect(url_for('view_athlete', athlete_id=athlete_id))
    
    athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    return render_template('edit_athlete.html', athlete=athlete)

@app.route('/athlete/<int:athlete_id>/renew', methods=['GET', 'POST'])
def renew_athlete(athlete_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        additional_days = int(request.form['days'])
        
        # Get current athlete data
        athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
        
        if not athlete:
            flash('Athlete not found!', 'danger')
            return redirect(url_for('athletes'))
        
        # Calculate new values
        current_days = athlete['days_remaining']
        new_days_remaining = current_days + additional_days
        original_days = athlete['days_remaining'] 
        
        # Update database
        conn.execute('''UPDATE athletes SET 
                      days_remaining = ?
                      WHERE id = ?''',
                    (new_days_remaining, athlete_id))
        conn.commit()
        conn.close()
        
        # Log activity
        log_activity(
            action="RENEWAL",
            details=f"Renewed membership for {athlete['first_name']} {athlete['last_name']} (ID: {athlete_id}) for {additional_days} days",
            athlete_id=athlete_id
        )
        
        flash(f'Membership renewed successfully for {additional_days} days!', 'success')
        return redirect(url_for('view_athlete', athlete_id=athlete_id))
    
    # GET request - show form
    athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    # Calculate end date
    start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
    end_date = (start_date + timedelta(days=athlete['days_remaining'])).strftime('%Y-%m-%d')
    
    athlete_data = {
        'id': athlete['id'],
        'first_name': athlete['first_name'],
        'last_name': athlete['last_name'],
        'days_remaining': athlete['days_remaining'],
        'end_date': end_date,
        'original_days': athlete['days_remaining']  
    }
    
    return render_template('renew_athlete.html', athlete=athlete_data)

@app.route('/athlete/<int:athlete_id>/delete', methods=['POST'])
def delete_athlete(athlete_id):
    conn = get_db_connection()
    
    # Get athlete info before deleting
    athlete = conn.execute('SELECT first_name, last_name FROM athletes WHERE id = ?', 
                         (athlete_id,)).fetchone()
    
    if athlete:
        conn.execute('DELETE FROM athletes WHERE id = ?', (athlete_id,))
        conn.commit()
        
        log_activity(
            action="DELETION",
            details=f"Deleted athlete: {athlete['first_name']} {athlete['last_name']} (ID: {athlete_id})",
            athlete_id=athlete_id
        )
        
        flash('Athlete deleted successfully!', 'success')
    else:
        flash('Athlete not found!', 'danger')
    
    conn.close()
    return redirect(url_for('athletes'))

@app.route('/history')
def history():
    search_query = request.args.get('search', '')
    action_type = request.args.get('action_type', '')
    
    conn = get_db_connection()
    
    query = '''SELECT activity_log.*, athletes.first_name, athletes.last_name
             FROM activity_log
             LEFT JOIN athletes ON activity_log.athlete_id = athletes.id
             WHERE 1=1'''
    
    params = []
    
    if search_query:
        query += ' AND (details LIKE ? OR athletes.first_name LIKE ? OR athletes.last_name LIKE ?)'
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param])
    
    if action_type:
        query += ' AND action = ?'
        params.append(action_type)
    
    query += ' ORDER BY timestamp DESC'
    
    activities = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('history.html', activities=activities, 
                         search_query=search_query, action_type=action_type)

if __name__ == '__main__':
    app.run(debug=True)