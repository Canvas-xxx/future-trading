import requests

def push_notify_message(token, message):
    headers = {'Authorization': 'Bearer ' + token}
    data = {'message': message}
    session = requests.Session()
    try:
        session.post('https://notify-api.line.me/api/notify', headers=headers, data=data)
    except:
        print('Error send notify')
