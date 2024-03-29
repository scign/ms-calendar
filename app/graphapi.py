import requests
import uuid
import json
from datetime import date, timedelta
from dateutil.parser import parse
import os
import csv
from flask import session, render_template

graph_endpoint = 'https://graph.microsoft.com/v1.0{0}'

# Generic API Sending
def make_api_call(method, url, payload = None, parameters = None):
    '''
    Constructs an API call to the Microsoft Graph API
    including a user agent, authorization and content type.
    The access token must have already been received and stored
    in session['access_token'].

    Parameters

    method : string value for the http method, currently supports
    GET, POST, DELETE and PATCH, not case sensitive
    
    url : string full URL to send the request to, including scheme
    
    payload : data to be sent in the request, translated
    internally using json.dumps(payload)
    
    parameters : dict of any additional params to be sent

    Returns
    
    requests.Response object
    '''
    # Send these headers with all API calls
    headers = {
        'User-Agent': 'python_tutorial/1.0',
        'Authorization': 'Bearer {0}'.format(session['access_token']),
        'Accept': 'application/json'
    }

    # Use these headers to instrument calls. Makes it easier
    # to correlate requests and responses in case of problems
    # and is a recommended best practice.
    request_id = str(uuid.uuid4())
    instrumentation = {
        'client-request-id': request_id,
        'return-client-request-id': 'true'
    }
    headers.update(instrumentation)
    
    response = None
    # to do: handle ConnectionError (if not connected)
    if (method.upper() == 'GET'):
        response = requests.get(url, headers = headers, params = parameters)
    elif (method.upper() == 'DELETE'):
        response = requests.delete(url, headers = headers, params = parameters)
    elif (method.upper() == 'PATCH'):
        headers.update({ 'Content-Type' : 'application/json' })
        response = requests.patch(url, headers = headers, data = json.dumps(payload), params = parameters)
    elif (method.upper() == 'POST'):
        headers.update({ 'Content-Type' : 'application/json' })
        response = requests.post(url, headers = headers, data = json.dumps(payload), params = parameters)

    return response

def error_wrap(resp):
    try:
        if resp.status_code == requests.codes.ok:
            return resp.json()
    except:
        pass
    return {
        'status_code': resp.status_code,
        'error_text': resp.text
    }

def get_me():
    # Use OData query parameters to control the results
    #  - Only return the displayName and mail fields
    query_parameters = {'$select': 'mail,displayName,jobTitle,businessPhones'}
    # to do: handle ConnectionError (if not connected)
    r = error_wrap(make_api_call(
        'GET', graph_endpoint.format('/me'),
        "", parameters = query_parameters
    ))
    return r

def load_rooms():
    rooms = []
    with open(os.path.join('app','data','rooms.csv'),'r') as f:
        freader = csv.DictReader(f, delimiter=',', quotechar='"')
        rooms = [line for line in freader]
    return rooms

def get_all_meetings(days=1):
    get_meetings_url = graph_endpoint.format('/me/calendar/getSchedule')
    rooms = load_rooms()
    body = {
        'schedules': [room['email'] for room in rooms],
        'startTime': {
            'dateTime': date.today().strftime('%Y-%m-%d'),
            'timeZone': 'Eastern Standard Time'
        },
        'endTime': {
            'dateTime': (date.today() + timedelta(days=days)).strftime('%Y-%m-%d'),
            'timeZone': 'Eastern Standard Time'
        },
        'availabilityViewInterval': 30
    }
    # to do: handle ConnectionError (if not connected)
    r = error_wrap(make_api_call(
        'POST', get_meetings_url,
        body
    ))
    return r

def get_my_meetings(days=1):
    get_meetings_url = graph_endpoint.format('/me/calendarview')
    get_meetings_url += '?StartDateTime=' + date.today().strftime('%Y-%m-%d') + 'T01:00:00'
    get_meetings_url += '&EndDateTime=' + (date.today() + timedelta(days=days+1)).strftime('%Y-%m-%d') + 'T01:00:00'
    # startdatetime=2020-02-24T22:29:28.248Z
    # & enddatetime=2020-03-02T22:29:28.248Z
    r = error_wrap(make_api_call(
        'GET', get_meetings_url
    ))
    return r

def get_convenient_slot(attendees, days):
    get_convenient_url = graph_endpoint.format('/me/calendar/getschedule')
    return None
