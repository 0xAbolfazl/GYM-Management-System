from requests import get, post
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())

API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_welcome_msg(number, name):
    base_url = 'https://edge.ippanel.com/v1'
    msg = f'''{name} عزیز به باشگاه کیاپارس خوش امدید\nhttps://midn.me/BT9Dml'''
    url = f'{base_url}/api/send/webservice?from=+983000505&message={msg}&to=+98{number}&apikey={API_KEY}'
    try:
        response = get(url=url)
        code = response.status_code
        if code == 200:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return True
        else:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return False
    except Exception as e:
        send_to_telegram_bot(f'Critical Error : \n{str(e)}')

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

def hbd(name, phone):
    base_url = 'https://edge.ippanel.com/v1'
    msg = f'''{name} زادروزت مبارک باد'''
    url = f'{base_url}/api/send/webservice?from=+983000505&message={msg}&to=+98{phone}&apikey={API_KEY}'
    try:
        response = get(url=url)
        code = response.status_code
        if code == 200:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return True
        else:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return False
    except Exception as e:
        send_to_telegram_bot(f'Critical Error : \n{str(e)}')

def end_date_reminder(name, phone):
    base_url = 'https://edge.ippanel.com/v1'
    msg = f'''{name} عزیز سررسید دوره باشگاه شما 3 روزدیگر فرامیرسد'''
    url = f'{base_url}/api/send/webservice?from=+983000505&message={msg}&to=+98{phone}&apikey={API_KEY}'
    try:
        response = get(url=url)
        code = response.status_code
        if code == 200:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return True
        else:
            send_to_telegram_bot(f'Message sender returned : {code}')
            return False
    except Exception as e:
        send_to_telegram_bot(f'Critical Error : \n{str(e)}')