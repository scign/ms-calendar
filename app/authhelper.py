from urllib.parse import quote, urlencode
import base64
import json
import time
import requests

from app import app
from flask import session, url_for, redirect

# Constant strings for OAuth2 flow
# The OAuth authority
authority = 'https://login.microsoftonline.com/' + app.config['AZURE_TENANT_ID']

# The authorize URL that initiates the OAuth2 client credential flow for admin consent
authorize_url = '{0}{1}'.format(authority, '/oauth2/v2.0/authorize?{0}')

# The token issuing endpoint
token_url = '{0}{1}'.format(authority, '/oauth2/v2.0/token')

# The scopes required by the app
# make sure these are added to the API Permissions section in the App Registration
scopes = [
    'openid',
    'offline_access',
    'User.Read',
    'Calendars.Read',
    'Calendars.Read.Shared'
]

def get_signin_url(redirect_uri):
    # Build the query parameters for the signin url
    params = {
        'client_id': app.config['AZURE_APP_ID'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(str(i) for i in scopes)
    }

    signin_url = authorize_url.format(urlencode(params))
    return signin_url

def get_token_from_code(auth_code, redirect_uri):
    post_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in scopes),
        'client_id': app.config['AZURE_APP_ID'],
        'client_secret': app.config['AZURE_APP_SECRET']
    }
    r = requests.post(token_url, data = post_data)
    try:
        token = r.json()
        store_tokens_in_session(token)
    except:
        print('Error retrieving token: {0} - {1}'.format(r.status_code, r.text))
    return r.status_code

def get_token_from_refresh_token(refresh_token, redirect_uri):
    post_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(str(i) for i in scopes),
        'client_id': app.config['AZURE_APP_ID'],
        'client_secret': app.config['AZURE_APP_SECRET']
    }
    r = requests.post(token_url, data = post_data)
    try:
        token = r.json()
        store_tokens_in_session(token)
    except:
        print('Error retrieving token: {0} - {1}'.format(r.status_code, r.text))
    return r.status_code

def get_access_token(redirect_uri):
    # get the current token and its expiration time from the session
    if 'access_token' not in session.keys():
        return None
    current_token = session['access_token']
    expiration = session['token_expires']
    now = int(time.time())
    if (current_token and now < expiration):
        # if there's a current token, and it's still good, return it
        return current_token
    else:
        # otherwise refresh it and return the new one
        if get_token_from_refresh_token(session['refresh_token'], redirect_uri) == requests.codes.ok:
            return session['access_token']
        else:
            return None

def store_tokens_in_session(token):
    session['access_token'] = token['access_token']
    session['refresh_token'] = token['refresh_token']
    session['token_expires'] = int(time.time()) + token['expires_in'] - 300
