import requests

def fetch_ttlock_token(data):
    url = 'https://euapi.ttlock.com/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, headers=headers, data=data)
    try:
        response.raise_for_status()
        return response.json()
    except Exception:
        return {'error': response.text, 'status_code': response.status_code}
