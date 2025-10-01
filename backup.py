import smtplib
import datetime
import os
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
TO_EMAIL = os.getenv('TO_EMAIL')

def send_db_backup():
    db_file = "/home/kiaparsg/gym/database.db"
    backup_dir = "/home/kiaparsg/backups"
    
    # create backup folder if not exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # creating backup file
    backup_filename = f"database_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # coping to backup path
        shutil.copy2(db_file, backup_path)
        print(f"Backup copied to: {backup_path}")
        
        # sending backup file via email
        send_backup_email(backup_path)
        
    except Exception as e:
        print(f"Error in backup process: {e}")

def send_backup_email(backup_file_path):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = TO_EMAIL
    msg['Subject'] = f"Database Backup - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    body = f"""
    Database backup attached.
    File: {os.path.basename(backup_file_path)}
    Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Size: {os.path.getsize(backup_file_path) / 1024:.2f} KB
    Backup Location: {backup_file_path}
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with open(backup_file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= "{os.path.basename(backup_file_path)}"'
        )
        msg.attach(part)
        
        # sending email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        
        print(f"Backup sent successfully to {TO_EMAIL}")
        
    except Exception as e:
        print(f"Error sending email: {e}")

def cleanup_old_backups(days=7):
    """deleting older backup (7 days)"""
    backup_dir = "/home/kiaparsg/backups"
    if not os.path.exists(backup_dir):
        return
    
    now = datetime.datetime.now()
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if (now - file_time).days > days:
                os.remove(file_path)
                print(f"Deleted old backup: {filename}")

if __name__ == "__main__":
    # backup
    send_db_backup()
    cleanup_old_backups(7)