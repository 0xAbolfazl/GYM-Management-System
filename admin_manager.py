import sqlite3
import hashlib

def create_database():
    # Connect to SQLite database (will be created if it doesn't exist)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create admins table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create trigger for updated_at
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_admin_timestamp
    AFTER UPDATE ON admins
    FOR EACH ROW
    BEGIN
        UPDATE admins SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END
    ''')
    
    # Sample admin data (in real app, use proper password hashing)
    admins = [
        {
            'username': 'admin1',
            'password': 'securepass123',  # In production, use proper hashing
            'first_name': 'Ali',
            'last_name': 'Mohammadi'
        },
        {
            'username': 'admin2',
            'password': 'strongpass456',  # In production, use proper hashing
            'first_name': 'Zahra',
            'last_name': 'Rahimi'
        }
    ]
    
    # Insert admin users with hashed passwords
    for admin in admins:
        # Hash the password (in production, use better hashing like bcrypt)
        hashed_password = hashlib.sha256(admin['password'].encode()).hexdigest()
        
        cursor.execute('''
        INSERT OR IGNORE INTO admins (username, password, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (admin['username'], hashed_password, admin['first_name'], admin['last_name']))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database created successfully with 2 admin users.")

if __name__ == "__main__":
    create_database()