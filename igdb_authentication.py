import requests
import os
from ast import literal_eval
import json

def authenticate_twitch():
    client_id = os.environ.get('TWITCH_ID')
    client_secret = os.environ.get('TWITCH_SECRET')
    url = f'https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'
    response = requests.post(url)
    if response.status_code == 200:
        content = response.content.decode('utf-8').replace("'", '"')
        data = literal_eval(content)
        with open('credentials/twitch_credentials.json', 'w') as f:
            json.dump(data, f, sort_keys=True, indent=3)
        return content

def get_token():
    with open('credentials/twitch_credentials.json', 'r') as f:
        credentials = json.load(f)
        f.close()
    return credentials['access_token']

if __name__ == '__main__':
    authenticate_twitch()