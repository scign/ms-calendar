import config
from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)

@app.route('/')
def login():
    sign_in_url = '#'  # stay on the same page
    context = {'signin_url': sign_in_url}
    return 'hello world!'
    #render_template('login.html', context)

if __name__ == '__main__':
    app.run()