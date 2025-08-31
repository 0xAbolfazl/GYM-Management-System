import sqlite3
from datetime import datetime, timedelta
import time
from sms import hbd, end_date_reminder

def get_athletes_with_birthday_today():
    try:
        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Get today's date in MM-DD format (month-day)
        today = datetime.now().strftime('%m-%d')
        
        # Query to retrieve data
        query = """
        SELECT first_name, phone 
        FROM athletes 
        WHERE gender = 'male' 
        AND strftime('%m-%d', birth_date) = ?
        """
        
        # Execute the query
        cursor.execute(query, (today,))
        
        # Fetch results
        results = cursor.fetchall()
        
        # Print results
        if results:
            print("Male athletes with birthday today:")
            print("-" * 40)
            for row in results:
                hbd(name=row[0], phone=row[1])
                print(f"Name: {row[0]}")
                print(f"Phone: {row[1]}")
                print("-" * 20)
        else:
            print("No male athletes found with birthday today.")
            
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        
    finally:
        # Close connection
        if conn:
            conn.close()

def send_reminder_to_ending_period():
    try:
        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Calculate the target date (3 days from now)
        target_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Query to find athletes whose period ends in exactly 3 days
        query = """
        SELECT first_name, phone 
        FROM athletes 
        WHERE gender = 'male' 
        AND date(start_date, '+' || original_days || ' days') = ?
        """
        
        # Execute the query
        cursor.execute(query, (target_date,))
        
        # Fetch results
        results = cursor.fetchall()
        
        # Send message to each athlete
        for row in results:
            name, phone = row
            end_date_reminder(name=name, phone=phone)
            print(name+" "+phone)
            
        print(f"Sent reminders to {len(results)} athletes")
            
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        
    finally:
        # Close connection
        if conn:
            conn.close()


def run_scheduler():
    while True:
        try:
            get_athletes_with_birthday_today()
            send_reminder_to_ending_period()
        except Exception as e:
            print(f"Error: {e}")  
        finally:
            time.sleep(24 * 60 * 60) 

if __name__ == "__main__":
    run_scheduler()
