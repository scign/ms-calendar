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

@app.route('/responses', methods=['GET','POST'])
def responses():
    if not logged_in():
        return redirect(url_for('login'))
    num_days = 1  # default value
    if request.method == 'POST':
        num_days = request.form['num-days']
    if request.method == 'GET' and 'days' in request.args.keys():
        num_days = request.args['days']
    if type(num_days) is str:
        try:
            num_days = int(num_days)
        except:
            num_days = 1
    
    meetings = get_my_meetings(days=num_days)
    if 'status_code' in meetings.keys():
        return handle_error(meetings)
    
    cols = [
        'id','showAs','start','end',
        'isCancelled','subject','isOrganizer',
        'location','organizer','attendees'
    ]
    df = pd.DataFrame(meetings['value'], columns=cols)
    df = df[(df.showAs.isin(['busy','tentative'])) & ~df.isCancelled]
    df['event_id'] = df.id.str[58:68] + df.id.str[-16:-2]
    df['start_time'] = df['start'].apply(lambda dt: parse(dt['dateTime'] + dt['timeZone']).astimezone(gettz('EST')))
    df['end_time'] = df['end'].apply(lambda dt: parse(dt['dateTime'] + dt['timeZone']).astimezone(gettz('EST')))
    df['duration'] = df.end_time - df.start_time
    df['start_time_text'] = df.start_time.apply(lambda t: t.strftime('%Y-%m-%d %H:%M'))
    df['end_time_text'] = df.end_time.apply(lambda t: t.strftime('%Y-%m-%d %H:%M'))
    df['room'] = df['location'].apply(lambda location: location['displayName'])
    attendee_responses = []
    response_summaries = []
    for i,event in df.iterrows():
        response_group = []
        response_summary = {}
        for attendee in event['attendees']:
            response_summary[attendee['status']['response']] = response_summary.get(attendee['status']['response'], 0) + 1
            response_group.append({
                'email': attendee['emailAddress']['address'],
                'response': attendee['status']['response'],
                'has_accepted': attendee['status']['response']=='accepted',
                'has_declined': attendee['status']['response']=='declined',
                'has_tentative': attendee['status']['response']=='tentativelyAccepted',
                'no_response': attendee['status']['response']=='none',
                'is_organizer': attendee['emailAddress']['address']==event['organizer']['emailAddress']['address']
            })
        attendee_responses.append(response_group)
        response_summaries.append({
            'accepted': "{}".format(response_summary.get('accepted', 0)),
            'tentative': "{}".format(response_summary.get('tentativelyAccepted', 0)),
            'declined': "{}".format(response_summary.get('declined', 0)),
            'none': "{}".format(response_summary.get('none', 0) - 1)  # organizer has response 'none'
        })
    df['responses'] = attendee_responses
    df['summary'] = response_summaries
    cols = [
        'id','subject','isOrganizer',
        'showAs','start_time_text','event_id',
        'duration','room','responses', 'summary'
    ]
    events = df[cols].to_dict(orient='records')
    context = {'events': events}
    return render_template('responses.html', **context)

if __name__ == '__main__':
    app.run()

'''
'@odata.etag', 'id', 'createdDateTime', 'lastModifiedDateTime',
'changeKey', 'categories', 'originalStartTimeZone',
'originalEndTimeZone', 'iCalUId', 'reminderMinutesBeforeStart',
'isReminderOn', 'hasAttachments', 'subject', 'bodyPreview',
'importance', 'sensitivity', 'isAllDay', 'isCancelled', 'isOrganizer',
'responseRequested', 'seriesMasterId', 'showAs', 'type', 'webLink',
'onlineMeetingUrl', 'recurrence', 'responseStatus', 'body', 'start',
'end', 'location', 'locations', 'attendees', 'organizer', 'start_time',
'end_time', 'duration', 'room'
'''
