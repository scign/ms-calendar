from flask import render_template, url_for, request, session, redirect

from app import app
from app.mylogger import log
from app.authhelper import get_signin_url, get_token_from_code, get_access_token
from app.graphapi import get_me, get_all_meetings, get_my_meetings

from dateutil.parser import parse
from dateutil.tz import gettz
import requests
import pandas as pd

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

def logged_in():
    redirect_uri = get_redirect_uri()
    access_token = get_access_token(redirect_uri)
    return access_token is not None

@app.route('/')
def login():
    if logged_in():
        return redirect(url_for('upcoming_meetings'))
    redirect_uri = get_redirect_uri()
    sign_in_url = get_signin_url(redirect_uri)
    context = {'signin_url': sign_in_url}
    return render_template('login.html', **context)

@app.route('/get_token')
def token():
    auth_code = request.args.get('code')
    get_token_from_code(auth_code, get_redirect_uri())
    return redirect(url_for('me'))

@app.route('/me')
def me():
    if not logged_in():
        return redirect(url_for('login'))
    user = get_me()
    if 'status_code' in user.keys():
        return handle_error(user)
    context = {'user': user}
    return render_template('profile.html', **context)

@app.route('/events', methods=['GET','POST'])
def upcoming_meetings():
    '''
    Get upcoming room bookings for all TCH meeting rooms
    '''
    # check we're signed in
    if not logged_in():
        return redirect(url_for('login'))
    num_days = 2  # default value
    if request.method == 'POST':
        num_days = request.form['num-days']
    
    meetings = get_all_meetings(days=num_days)
    if 'status_code' in meetings.keys():
        return handle_error(meetings)
    
    meetings = meetings['value']
    events = []
    # get details for each room booking
    for schedule in meetings:
        for item in schedule['scheduleItems']:
            start_time = parse(item['start']['dateTime'] + item['start']['timeZone'])
            end_time = parse(item['end']['dateTime'] + item['end']['timeZone'])
            duration = end_time - start_time
            events.append({
                'room': schedule['scheduleId'][:13].upper(),
                'subject': item['subject'],
                'start_time': start_time.astimezone(gettz('EST')).strftime('%d %b, %H:%M'),
                'end_time': end_time.astimezone(gettz('EST')).strftime('%d %b, %H:%M'),
                'room_email': schedule['scheduleId'],
                'duration': duration
            })
    events.sort(key=lambda x: x['start_time'] + x['room'])
    context = {'events': events}
    return render_template('meetings.html', **context)

@app.route('/declines')
def declines():
    # not fully yet implemented. for now redirect
    return redirect(url_for('login'))
    
    if not logged_in():
        return redirect(url_for('login'))
    meetings = get_my_meetings(days=3)
    if 'status_code' in meetings.keys():
        return handle_error(meetings)
    
    context = {'meetings': meetings}
    return render_template('profile.html', **context)

if __name__ == '__main__':
    app.run()
