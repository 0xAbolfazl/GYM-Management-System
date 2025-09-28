from requests import get, post
from dotenv import load_dotenv, find_dotenv
import os
import requests


load_dotenv(find_dotenv())

API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://edge.ippanel.com/v1"  
FROM_NUMBER = "+983000505"

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
            print("Send successfully")
            send_to_telegram_bot("Send successfully for welcome")
            return response.json()
        else:
            print(f"Error status code: {response.status_code}")
            print(f"response: {response.text}")
            send_to_telegram_bot(f"Error status code: {response.status_code}")
            send_to_telegram_bot(f"response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        send_to_telegram_bot(f"Error Connecting to server: {e}")
        print(f"Error Connecting to server: {e}")
        return None

def welcome_msg(number, name):
    msg_sender(number, name, '9d3a2cc6z9ifzzk')

def end_date_reminder_msg(number, name):
    msg_sender(number, name, '0gkloqbefruu2mq')

def birthdate_msg(number, name):
    msg_sender(number, name, 'd2wk80fawdqp45b')

if __name__ == "__main__":
    birthdate_msg('09046081703', 'Abolfazl')