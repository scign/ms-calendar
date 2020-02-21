from flask import Flask
import config

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)

from app import routes
