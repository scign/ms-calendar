from app.mylogger import log
from flask import render_template

from app import app

@app.route('/')
def login():
    sign_in_url = '#'  # stay on the same page
    context = {'signin_url': sign_in_url}
    log("DEBUG", 'Rendering template')
    return render_template('login.html', context=context)

if __name__ == '__main__':
    app.run()
