from requests import get, post
from dotenv import load_dotenv, find_dotenv
import os
import requests
import threading
from time import sleep


load_dotenv(find_dotenv())

API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://edge.ippanel.com/v1"  
FROM_NUMBER = "+983000505"
WELCOME_PATTERN_ID = os.getenv('WELCOME_PATTERN_ID')
END_DATE_PATTERN_ID = os.getenv('END_DATE_PATTERN_ID')
BIRTHDATE_PATTERN_ID = os.getenv('BIRTHDATE_PATTERN_ID')

def add(txt):
    try:
        print(txt)
        log(txt)
    except Exception:
        pass

def log(text):
    """
    Write text to a file. If file doesn't exist, it will be created.
    If file exists, new text will be appended to the end.
    
    Args:
        filename (str): Name of the file
        text (str): Text to be written to the file
    """
    try:
        filename = 'applog.txt'
        with open(filename, 'a', encoding='utf-8') as file:
            file.write(text + '\n')  # Add new line
        print(f"Text successfully written to file '{filename}'.")
    except Exception as e:
        print(f"Error writing to file: {str(e)}")

def send_to_telegram_bot(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/SendMessage?chat_id={CHAT_ID}&text={message}"
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

def msg_sender(phone_number, name, pattern_code):
    payload = {
        "sending_type": "pattern",
        "from_number": FROM_NUMBER,
        "code" : pattern_code,
        "recipients": [f"+98{str(phone_number)[1:]}"],
        "params": {
    "name": name
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": API_KEY 
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/send",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            add("Send successfully for welcome")
            return response.json()
        else:
            add(f"Error status code: {response.status_code}")
            add(f"response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        add(f"Error Connecting to server: {e}")
        return None

def welcome_msg(number, name):
    msg_sender(number, name, WELCOME_PATTERN_ID)

def end_date_reminder_msg(number, name):
    msg_sender(number, name, END_DATE_PATTERN_ID)

def birthdate_msg(number, name):
    msg_sender(number, name, BIRTHDATE_PATTERN_ID)

if __name__ == "__main__":
    welcome_msg('09040000000', 'name')