from kavenegar import *
api = KavenegarAPI('Your API Key')
params = {
        'sender': '1000xxxx',
        'receptor' : '0919xxxxxx',
        'message' : "Hello Python!"
}   
response = api.sms_send(params)