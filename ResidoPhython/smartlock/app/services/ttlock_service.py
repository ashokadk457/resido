import requests

def fetch_ttlock_token(client_id, client_secret, username, password):
    url = 'https://euapi.ttlock.com/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'clientId': client_id,
        'clientSecret': client_secret,
        'username': username,
        'password': password
    }
    response = requests.post(url, headers=headers, data=data)
    try:
        response.raise_for_status()
        return response.json()
    except Exception:
        return {'error': response.text, 'status_code': response.status_code}
