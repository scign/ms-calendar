from flask import render_template, url_for, request, session, redirect

from app import app
from app.mylogger import log
from app.authhelper import get_signin_url, get_token_from_code, get_access_token
from app.graphapi import get_me, get_all_meetings

from dateutil.parser import parse
from dateutil.tz import gettz
import requests

# should be pulled from the config
assert(app.config['AZURE_TENANT_ID'] is not None)
assert(app.config['AZURE_APP_ID'] is not None)
assert(app.config['AZURE_APP_SECRET'] is not None)

def get_redirect_uri():
    '''
    Return the location to pass to the MS OAuth2 framework
    '''
    return url_for('token', _external=True, _scheme='https')

def handle_error(resp):
    suggestions = {
        requests.codes.bad_request: 'There\'s something wrong with the request',
        requests.codes.unauthorized: 'Authorization failure. Please refresh the page and sign in again.',
        requests.codes.not_found: 'Microsoft Graph endpoint not found. Microsoft might have made a breaking change. Typical.',
        requests.codes.proxy_authentication_required: 'Either authenticate to the proxy you\'re connected to or get out from behind it.',
        requests.codes.timeout: 'Request timed out. Please try again.'
    }
    if resp['status_code'] == requests.codes.unauthorized:
        return redirect(url_for('login'))
    if resp['status_code'] in suggestions.keys():
        resp['suggestion'] = suggestions[resp['status_code']]
    else:
        resp['suggestion'] = 'I\'ll leave it to you to figure out what to do here.'
    return render_template('error.html', **resp)

@app.route('/')
def login():
    redirect_uri = get_redirect_uri()
    access_token = get_access_token(redirect_uri)
    if access_token is None:
        sign_in_url = get_signin_url(redirect_uri)
        context = {'signin_url': sign_in_url}
        return render_template('login.html', **context)
    else:
        return redirect(url_for('upcoming_meetings'))

@app.route('/get_token')
def token():
    auth_code = request.args.get('code')
    get_token_from_code(auth_code, get_redirect_uri())
    return redirect(url_for('me'))

@app.route('/me')
def me():
    user = get_me()
    if 'status_code' in user.keys():
        return handle_error(user)
    return 'Hi {} {}, I see that your email address is {}'.format(user['givenName'], user['surname'], user['mail'])

@app.route('/events')
def upcoming_meetings():
    meetings = get_all_meetings(days=2)
    if 'status_code' in meetings.keys():
        return handle_error(meetings)
    meetings = meetings['value']
    events = []
    for schedule in meetings:
        for item in schedule['scheduleItems']:
            start_time = parse(item['start']['dateTime'] + item['start']['timeZone'])
            end_time = parse(item['end']['dateTime'] + item['end']['timeZone'])
            duration = end_time - start_time
            events.append({
                'room': item['location'],
                'subject': item['subject'],
                'start_time': start_time.astimezone(gettz('EST')).strftime('%d %b, %H:%M'),
                'end_time': end_time.astimezone(gettz('EST')).strftime('%d %b, %H:%M'),
                'room_email': schedule['scheduleId'],
                'duration': duration
            })
    context = {'events': events}
    return render_template('meetings.html', **context)

if __name__ == '__main__':
    app.run()
