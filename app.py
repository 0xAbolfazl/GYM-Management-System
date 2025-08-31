from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import random
from functools import wraps
import hashlib
from datetime import datetime
from time import sleep
import jdatetime
from sms import send_welcome_msg

app = Flask(__name__)
app.secret_key = 'gymsecret'  # Change this to a secure secret key

def convert_persian_to_gregorian(persian_date_str):
    """
    Convert Persian (Solar Hijri) date string to Gregorian date string.
    
    Args:
        persian_date_str (str): Persian date in format 'YYYY/MM/DD'
    
    Returns:
        str: Gregorian date in format 'YYYY-MM-DD'
    
    Example:
        Input: '1404/05/28'
        Output: '2025-08-27'
    """
    try:
        # Parse Persian date string
        persian_date = jdatetime.datetime.strptime(persian_date_str, "%Y/%m/%d")
        
        # Convert to Gregorian
        gregorian_date = persian_date.togregorian()
        
        # Format as YYYY-MM-DD
        return gregorian_date.strftime("%Y-%m-%d")
        
    except ValueError as e:
        raise ValueError(f"Invalid date format or date. Expected 'YYYY/MM/DD'. Error: {e}")
    except Exception as e:
        raise Exception(f"Conversion error: {e}")

def convert_gregorian_to_persian(gregorian_date_str):
    """
    Convert Gregorian date string to Persian (Solar Hijri) date string.
    
    Args:
        gregorian_date_str (str): Gregorian date in format 'YYYY-MM-DD'
    
    Returns:
        str: Persian date in format 'YYYY/MM/DD'
    
    Example:
        Input: '2025-08-20'
        Output: '1404/05/28'
    """
    try:
        # Parse Gregorian date string
        gregorian_date = datetime.strptime(gregorian_date_str, "%Y-%m-%d")
        
        # Convert to Persian date
        persian_date = jdatetime.date.fromgregorian(
            year=gregorian_date.year,
            month=gregorian_date.month,
            day=gregorian_date.day
        )
        
        # Format as YYYY/MM/DD
        return persian_date.strftime("%Y/%m/%d")
        
    except ValueError as e:
        raise ValueError(f"Invalid date format. Expected 'YYYY-MM-DD'. Error: {e}")
    except Exception as e:
        raise Exception(f"Conversion error: {e}")

# Database Helper Functions
def get_db_connection():
    conn = sqlite3.connect('database.db', timeout=30) 
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')  
    return conn

def execute_with_retry(conn, query, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return conn.execute(query, params)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                sleep(0.1 + random() * 0.1)  
                continue
            raise

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
    
    try:
        # Athletes table
        conn.execute('''CREATE TABLE IF NOT EXISTS athletes
                    (id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    emergency_phone TEXT,
                    father_name TEXT,
                    birth_date TEXT,
                    registration_date TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    original_days INTEGER NOT NULL)''')
        
        # Activity log table
        conn.execute('''CREATE TABLE IF NOT EXISTS activity_log
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    athlete_id INTEGER,
                    FOREIGN KEY(athlete_id) REFERENCES athletes(id))''')
        
        # Attendance table
        conn.execute('''CREATE TABLE IF NOT EXISTS attendance
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      athlete_id INTEGER NOT NULL,
                      check_in_time TEXT NOT NULL,
                      check_out_time TEXT,
                      date TEXT NOT NULL,
                      FOREIGN KEY(athlete_id) REFERENCES athletes(id))''')
        
        # create index 
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_attendance_athlete_date 
            ON attendance(athlete_id, date)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_attendance_check_out 
            ON attendance(check_out_time)
        ''')
        
        conn.commit()
    finally:
        conn.close()

def get_today_attendance_stats(gender, date_filter):
    conn = get_db_connection()
    try:
        # Get all active athletes first
        athletes = execute_with_retry(conn, '''
            SELECT id, start_date, original_days 
            FROM athletes 
            WHERE gender = ?
        ''', (gender,)).fetchall()
        
        # Filter active athletes in Python
        active_athletes = []
        for athlete in athletes:
            start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
            end_date = start_date + timedelta(days=athlete['original_days'])
            remaining_days = (end_date - datetime.now()).days 
            remaining_days = remaining_days if remaining_days >= 0 else 0
            
            if remaining_days > 0:
                active_athletes.append(athlete['id'])
        
        total_active = len(active_athletes)
        
        if not active_athletes:
            return {
                'present': 0,
                'active': 0,
                'absent': 0
            }
        
        # Number of attendees on selected date (only active athletes)
        present = execute_with_retry(conn, '''
            SELECT COUNT(DISTINCT a.id) 
            FROM attendance att
            JOIN athletes a ON att.athlete_id = a.id
            WHERE att.date = ? AND a.gender = ? AND a.id IN ({})
        '''.format(','.join('?' * len(active_athletes))), 
        [date_filter, gender] + active_athletes).fetchone()[0]
        
        # Active sessions (checked in but not checked out) - only active athletes
        active = execute_with_retry(conn, '''
            SELECT COUNT(DISTINCT a.id) 
            FROM attendance att
            JOIN athletes a ON att.athlete_id = a.id
            WHERE att.date = ? AND a.gender = ? AND att.check_out_time IS NULL AND a.id IN ({})
        '''.format(','.join('?' * len(active_athletes))), 
        [date_filter, gender] + active_athletes).fetchone()[0]
        
        absent = total_active - present
        
        return {
            'present': present,
            'active': active,
            'absent': absent
        }
    finally:
        conn.close()

def get_attendance_records(gender, date_filter, search_query=None):
    conn = get_db_connection()
    try:
        query = '''
            SELECT 
                a.id as athlete_id,
                a.first_name,
                a.last_name,
                a.start_date,
                a.original_days,
                att.check_in_time,
                att.check_out_time,
                att.date
            FROM athletes a
            LEFT JOIN (
                SELECT athlete_id, MAX(id) as max_id
                FROM attendance
                WHERE date = ?
                GROUP BY athlete_id
            ) latest ON a.id = latest.athlete_id
            LEFT JOIN attendance att ON att.id = latest.max_id
            WHERE a.gender = ?
        '''
        
        params = [date_filter, gender]
        
        if search_query:
            query += '''
                AND (a.first_name LIKE ? OR 
                     a.last_name LIKE ? OR 
                     a.id = ?)
            '''
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_query])
        
        query += ' ORDER BY a.first_name, a.last_name'
        
        records = execute_with_retry(conn, query, params).fetchall()
        
        attendance_data = []
        for record in records:
            start_date = datetime.strptime(record['start_date'], '%Y-%m-%d')
            end_date = start_date + timedelta(days=record['original_days'])
            remaining_days = (end_date - datetime.now()).days 
            remaining_days = remaining_days if remaining_days >= 0 else 0
            
            if remaining_days > 0:
                status = "absent"
                duration = None
                
                if record['check_in_time']:
                    if record['check_out_time']:
                        status = "present"
                        # Calculate duration
                        check_in = datetime.strptime(record['check_in_time'], '%Y-%m-%d %H:%M:%S')
                        check_out = datetime.strptime(record['check_out_time'], '%Y-%m-%d %H:%M:%S')
                        delta = check_out - check_in
                        hours, remainder = divmod(delta.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        duration = f"{hours}h {minutes}m"
                    else:
                        status = "active"
                
                attendance_data.append({
                    'athlete_id': record['athlete_id'],
                    'name': f"{record['first_name']} {record['last_name']}",
                    'check_in': record['check_in_time'],
                    'check_out': record['check_out_time'],
                    'duration': duration,
                    'status': status
                })
        
        return attendance_data
    finally:
        conn.close()

from datetime import datetime, timedelta

def get_active_athletes(gender):
    conn = get_db_connection()
    try:
        athletes = execute_with_retry(conn, '''
            SELECT id, first_name, last_name, start_date, original_days 
            FROM athletes 
            WHERE gender = ?
            ORDER BY first_name, last_name
        ''', (gender,)).fetchall()
        
        active_athletes = []
        for athlete in athletes:
            start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
            end_date = start_date + timedelta(days=athlete['original_days'])
            remaining_days = (end_date - datetime.now()).days 
            
            if remaining_days > 0:
                active_athletes.append(athlete) 
        
        return active_athletes
        
    finally:
        conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Initialize the database
init_db()

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user:
            user_dict = dict(user)
            if user_dict['password'] == hashlib.sha256(password.encode()).hexdigest():
                session['logged_in'] = True
                session['username'] = user_dict['username']
                session['full_name'] = f"{user_dict['first_name']} {user_dict['last_name']}"
                session['gender'] = f'{user_dict["gender"]}'
                
                log_activity("LOGIN", f"User {username} logged in")
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
        
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/')
@login_required
def home():
    conn = get_db_connection()
    gender = session['gender']
    
    # Get all athletes for this gender
    athletes = conn.execute(
        "SELECT id, first_name, last_name, start_date, original_days, registration_date FROM athletes WHERE gender = ?",
        (gender,)
    ).fetchall()
    
    # Process athletes to calculate actual remaining days
    active_athletes = []
    expiring_48h = []
    expiring_soon_count = 0
    recent_registrations_count = 0
    
    # Calculate 7 days ago for recent registrations
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    for athlete in athletes:
        start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=athlete['original_days'])
        remaining_days = (end_date - datetime.now()).days 
        remaining_days = remaining_days if remaining_days >= 0 else 0
            
            # Check if expiring in less than 48 hours
        if remaining_days <= 2:
                expiring_48h.append({
                    'first_name': athlete['first_name'],
                    'last_name': athlete['last_name'],
                    'start_date': athlete['start_date'],
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'start_date_shamsi': convert_gregorian_to_persian(athlete['start_date']),
                    'end_date_shamsi': convert_gregorian_to_persian(end_date.strftime('%Y-%m-%d')),
                    'days_remaining': remaining_days,
                    'original_days': athlete['original_days']
                })
        # Check if athlete is active
        if remaining_days > 0:
            active_athletes.append(athlete)            
            # Count expiring soon (less than 7 days)
            if remaining_days < 7:
                expiring_soon_count += 1
        
        # Count recent registrations (last 7 days)
        if athlete['registration_date']:
            registration_date = datetime.strptime(athlete['registration_date'], '%Y-%m-%d %H:%M:%S')
            if registration_date > seven_days_ago:
                recent_registrations_count += 1
    
    stats = {
        'total_athletes': len(athletes),
        'active_athletes': len(active_athletes),
        'expiring_soon': expiring_soon_count,
        'recent_registrations': recent_registrations_count,
        'expiring_48h': expiring_48h,
        'expiring_48h_count': len(expiring_48h)
    }
    
    conn.close()
    return render_template('home.html', **stats)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        athlete_id = generate_unique_id()
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        emergency_phone = request.form.get('emergency_phone')
        father_name = request.form.get('father_name')
        birth_date_shamsi = request.form.get('birth_date')
        birth_date = convert_persian_to_gregorian(birth_date_shamsi)
        days = int(request.form['days'])
        start_date_shamsi = request.form.get('start_date')# or datetime.now().strftime('%Y-%m-%d')
        start_date = convert_persian_to_gregorian(start_date_shamsi)
        gender = session['gender']
        
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO athletes 
                      (id, first_name, last_name, phone, emergency_phone, father_name, 
                       birth_date, registration_date, start_date, original_days, gender)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (athlete_id, first_name, last_name, phone, emergency_phone, father_name,
                     birth_date, registration_date, start_date, days, gender))
        conn.commit()
        conn.close()
        
        log_activity(
            action="REGISTRATION",
            details=f"Registered new athlete: {first_name} {last_name} (ID: {athlete_id}) for {days} days",
            athlete_id=athlete_id
        )
        
        flash('Athlete registered successfully!', 'success')
        try:
            send_welcome_msg(str(first_name))
        except Exception:
            pass
        return redirect(url_for('athletes'))
    today = jdatetime.date.today()

    return render_template('register.html', default_start=today.strftime("%Y/%m/%d"))

@app.route('/athletes')
@login_required
def athletes():
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    gender = session['gender']
    if search_query:
        query = '''SELECT * FROM athletes 
                 WHERE gender = ? AND id = ? OR 
                       first_name LIKE ? OR 
                       last_name LIKE ? OR
                       first_name || ' ' || last_name LIKE ?
                 ORDER BY start_date DESC'''
        search_param = f"%{search_query}%"
        athletes_data = conn.execute(query, (gender, search_query, search_param, search_param, search_param)).fetchall()
    else:
        athletes_data = conn.execute('SELECT * FROM athletes WHERE gender = ? ORDER BY start_date DESC', (gender, )).fetchall()
    
    athletes = []
    for athlete in athletes_data:
        start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=athlete['original_days'])
        remaining_days = (end_date - datetime.now()).days
        remaining_days = max(0, remaining_days)
        
        athletes.append({
            'id': athlete['id'],
            'first_name': athlete['first_name'],
            'last_name': athlete['last_name'],
            'phone': athlete['phone'],
            'registration_date': athlete['registration_date'],
            'start_date': athlete['start_date'],
            'registration_date_shamsi' : convert_gregorian_to_persian(athlete['registration_date'].split(' ')[0]),
            'end_date': end_date.strftime('%Y-%m-%d'), 
            'end_date_shamsi': convert_gregorian_to_persian((datetime.strptime(athlete['start_date'], '%Y-%m-%d') + timedelta(days=athlete['original_days'])).strftime('%Y-%m-%d')),
            'days_remaining': remaining_days,
            'original_days': athlete['original_days']
        })
    
    conn.close()
    return render_template('athletes.html', 
                         athletes=athletes, 
                         search_query=search_query,
                         datetime=datetime,  
                         timedelta=timedelta) 

@app.route('/athlete/<int:athlete_id>')
@login_required
def view_athlete(athlete_id):
    conn = get_db_connection()
    athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
    end_date = start_date + timedelta(days=athlete['original_days'])
    
    athlete_data = {
        'id': athlete['id'],
        'first_name': athlete['first_name'],
        'last_name': athlete['last_name'],
        'phone': athlete['phone'],
        'emergency_phone': athlete['emergency_phone'],
        'father_name': athlete['father_name'],
        'birth_date': athlete['birth_date'],
        'birth_date_shamsi': convert_gregorian_to_persian(athlete['birth_date']),
        'registration_date': athlete['registration_date'],
        'registration_date_shamsi': convert_gregorian_to_persian(athlete['registration_date'].split(' ')[0]),
        'start_date': athlete['start_date'],
        'start_date_shamsi': convert_gregorian_to_persian(athlete['start_date']),
        'end_date': end_date.strftime('%Y-%m-%d'),  
        'end_date_shamsi': convert_gregorian_to_persian(end_date.strftime('%Y-%m-%d')),
        'days_remaining': max(0, (end_date - datetime.now()).days),
        'original_days': athlete['original_days']
    }
    
    return render_template('view_athlete.html', athlete=athlete_data)

@app.route('/athlete/<int:athlete_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_athlete(athlete_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        emergency_phone = request.form.get('emergency_phone')
        father_name = request.form.get('father_name')
        birth_date = convert_persian_to_gregorian(request.form.get('birth_date'))
        
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
    athlete = dict(athlete)
    athlete['birth_date_shamsi'] = convert_gregorian_to_persian(athlete['birth_date'])
    athlete['registration_date_shamsi'] = convert_gregorian_to_persian(athlete['registration_date'][0:10])
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    return render_template('edit_athlete.html', athlete=athlete)

@app.route('/athlete/<int:athlete_id>/renew', methods=['GET', 'POST'])
@login_required
def renew_athlete(athlete_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        additional_days = int(request.form['days'])
        
        # Get current athlete data
        athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
        
        if not athlete:
            flash('Athlete not found!', 'danger')
            return redirect(url_for('athletes'))
        
        # FIXED: Calculate remaining days based on current date, not original start date
        start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=athlete['original_days'])
        remaining_days = (end_date - datetime.now()).days
        remaining_days = max(0, remaining_days)
        
        # If membership has expired (negative days), reset start date to today
        if remaining_days <= 0:
            # For expired memberships, start fresh from today
            new_start_date = datetime.now().strftime('%Y-%m-%d')
            new_days_remaining = additional_days
        else:
            # For active memberships, add days to existing balance
            new_start_date = athlete['start_date']
            new_days_remaining = athlete['original_days'] + additional_days
        
        # Update database with new values
        conn.execute('''UPDATE athletes SET 
                      original_days = ?, start_date = ?
                      WHERE id = ?''',
                    (new_days_remaining, new_start_date, athlete_id))
        conn.commit()
        conn.close()
        
        # Log activity
        log_activity(
            action="RENEWAL",
            details=f"Renewed membership for {athlete['first_name']} {athlete['last_name']} (ID: {athlete_id}) for {additional_days} days. New total: {new_days_remaining} days",
            athlete_id=athlete_id
        )
        
        flash(f'Membership renewed successfully for {additional_days} days! Total days now: {new_days_remaining}', 'success')
        return redirect(url_for('view_athlete', athlete_id=athlete_id))
    
    # GET request - show form
    athlete = conn.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,)).fetchone()
    conn.close()
    
    if not athlete:
        flash('Athlete not found!', 'danger')
        return redirect(url_for('athletes'))
    
    # Calculate end date based on current status
    start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
    end_date = (start_date + timedelta(days=athlete['original_days']))
    remaining_days = max(0, (end_date - datetime.now()).days)

    athlete_data = {
        'id': athlete['id'],
        'first_name': athlete['first_name'],
        'last_name': athlete['last_name'],
        'days_remaining': remaining_days,
        'end_date': end_date,
        'end_date_shamsi' : convert_gregorian_to_persian(str(end_date).split(' ')[0])+" "+str(end_date).split(' ')[1],
        'original_days': athlete['original_days'],
        'is_expired': remaining_days <= 0  # Add flag for expired status
    }
    
    return render_template('renew_athlete.html', athlete=athlete_data)

@app.route('/athlete/<int:athlete_id>/delete', methods=['POST'])
@login_required
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
@login_required
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


@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    gender = session['gender']
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id')
        action = request.form.get('action')
        
        if not athlete_id or not action:
            flash('Invalid request', 'danger')
            return redirect(url_for('attendance'))

        conn = None
        try:
            conn = get_db_connection()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Checking the existence of the athlete and whether she is active
            athlete = execute_with_retry(conn, '''
                            SELECT id, start_date, original_days FROM athletes 
                            WHERE id = ? AND gender = ?
                            LIMIT 1
                        ''', (athlete_id, gender)).fetchone()

            if athlete:
                start_date = datetime.strptime(athlete['start_date'], '%Y-%m-%d')
                end_date = start_date + timedelta(days=athlete['original_days'])
                remaining_days = (end_date - datetime.now()).days 
                remaining_days = remaining_days if remaining_days >= 0 else 0
                
                if remaining_days <= 0:
                    athlete = None  
            
            if not athlete:
                flash('Athlete not found or inactive!', 'danger')
                return redirect(url_for('attendance'))

            if action == 'check_in':
                # Check if the athlete has already checked in today
                existing = execute_with_retry(conn, '''
                    SELECT 1 FROM attendance 
                    WHERE athlete_id = ? AND date = ? AND check_out_time IS NULL
                    LIMIT 1
                ''', (athlete_id, today)).fetchone()
                
                if existing:
                    flash('Athlete is already checked in today!', 'warning')
                else:
                    execute_with_retry(conn, '''
                        INSERT INTO attendance (athlete_id, check_in_time, date)
                        VALUES (?, ?, ?)
                    ''', (athlete_id, current_time, today))
                    conn.commit()
                    flash('Check-in recorded successfully!', 'success')
                    log_activity("CHECK_IN", f"Athlete {athlete_id} checked in", athlete_id)

            elif action == 'check_out':
                # Find the last check-in without checking out
                record = execute_with_retry(conn, '''
                    SELECT id FROM attendance 
                    WHERE athlete_id = ? AND date = ? AND check_out_time IS NULL
                    ORDER BY check_in_time DESC LIMIT 1
                ''', (athlete_id, today)).fetchone()
                
                if not record:
                    flash('No active check-in found for this athlete today!', 'warning')
                else:
                    execute_with_retry(conn, '''
                        UPDATE attendance 
                        SET check_out_time = ? 
                        WHERE id = ?
                    ''', (current_time, record['id']))
                    conn.commit()
                    flash('Check-out recorded successfully!', 'success')
                    log_activity("CHECK_OUT", f"Athlete {athlete_id} checked out", athlete_id)

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                flash('System is busy. Please try again in a moment.', 'warning')
            else:
                flash('Database error occurred', 'danger')
                app.logger.error(f"Database error: {str(e)}")
            if conn:
                conn.rollback()
        
        except Exception as e:
            flash('An error occurred while processing your request', 'danger')
            app.logger.error(f"Error in attendance route: {str(e)}")
            if conn:
                conn.rollback()
        
        finally:
            if conn:
                conn.close()
        
        return redirect(url_for('attendance'))
    
    # GET request handling
    date_filter = request.args.get('date', today)
    search_query = request.args.get('search', '').strip() or None
    
    stats = get_today_attendance_stats(gender, date_filter)
    
    records = get_attendance_records(gender, date_filter, search_query)
    
    active_athletes = get_active_athletes(gender)
    
    return render_template('attendance.html',
                         stats=stats,
                         attendance_data=records,
                         active_athletes=active_athletes,
                         date_filter=date_filter,
                         search_query=search_query or '',
                         datetime=datetime,
                         now=datetime.now())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)