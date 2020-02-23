import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    AZURE_APP_ID = os.environ.get('AZURE_APP_ID', '')
    AZURE_APP_SECRET = os.environ.get('AZURE_APP_SECRET', '')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')
    SECRET_KEY = AZURE_APP_SECRET


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True