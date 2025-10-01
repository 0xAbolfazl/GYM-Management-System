import sqlite3
from datetime import datetime, timedelta
import time
import os
import shutil
from sms import birthdate_msg, end_date_reminder_msg
from requests import post
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def add(txt):
    try:
        print(txt)
        send_to_telegram_bot(txt)
    except Exception:
        pass

def create_database_backup():
    """
    Create a backup copy of the database before operations.
    """
    original_db = 'database.db'
    backup_db = 'database_backup.db'
    
    try:
        # Check if original database exists
        if os.path.exists(original_db):
            # Create backup (overwrite if exists)
            shutil.copy2(original_db, backup_db)
            add(f"Database backup created: {backup_db}")
            return backup_db
        else:
            add(f"Original database '{original_db}' not found.")
            return original_db
    except Exception as e:
        add(f"[ERROR] Failed to create database backup: {str(e)}")
        return original_db

def get_athletes_with_birthday_today():
    db_path = create_database_backup()
    
    try:
        # Connect to the backup database
        conn = sqlite3.connect(db_path)
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
            add("Male athletes with birthday today:")
            add("-" * 40)
            for row in results:
                birthdate_msg(name=row[0], number=row[1])
                add(f"Name: {row[0]}")
                add(f"Phone: {row[1]}")
                add("-" * 20)
        else:
            add("No male athletes found with birthday today.")
            
    except sqlite3.Error as e:
        add(f"Database connection error: {e}")
        
    finally:
        # Close connection
        if conn:
            conn.close()

def send_reminder_to_ending_period():
    db_path = create_database_backup()
    
    try:
        # Connect to the backup database
        conn = sqlite3.connect(db_path)
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
            end_date_reminder_msg(name=name, number=phone)
            print(name+" "+phone)
            
        add(f"Sent reminders to {len(results)} athletes")
            
    except sqlite3.Error as e:
        add(f"Database connection error: {e}")
        
    finally:
        # Close connection
        if conn:
            conn.close()

def send_to_telegram_bot(msg: str) -> None:
    """
    Send message to Telegram bot.
    
    Args:
        msg: Message to send
        chatid: Telegram chat ID
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/SendMessage?chat_id={CHAT_ID}&text={msg}"
        sender = "https://www.httpdebugger.com/tools/ViewHttpHeaders.aspx"
        payload = {
            "UrlBox": url,
            "AgentList": "Mozilla Firefox",
            "VersionsList": "HTTP/1.1",
            "MethodList": "POST"
        }
        response = post(sender, payload)
        print(f"Telegram message sent. Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {str(e)}")

def cleanup_backup():
    """
    Remove the backup database file after operations.
    """
    backup_db = 'database_backup.db'
    try:
        if os.path.exists(backup_db):
            os.remove(backup_db)
            print(f"Backup database cleaned up: {backup_db}")
    except Exception as e:
        print(f"[WARNING] Could not remove backup database: {str(e)}")

def run_scheduler():
    try:
        # while True:
        #     get_athletes_with_birthday_today()
        #     send_reminder_to_ending_period()
        #     cleanup_backup()  # Cleanup after each cycle
        #     time.sleep(24 * 60 * 60)
        
        get_athletes_with_birthday_today()
        send_reminder_to_ending_period()
        
    finally:
        # Ensure cleanup happens even if there's an error
        cleanup_backup()

if __name__ == "__main__":
    run_scheduler()