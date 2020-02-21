# from mylogger import log
import logging
from flask import render_template

from app import app

@app.route('/')
def login():
    sign_in_url = '#'  # stay on the same page
    context = {'signin_url': sign_in_url}
    logging.info('Rendering template')
    return render_template('login.html', context)

if __name__ == '__main__':
    app.run()
