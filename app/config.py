import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    AZURE_APP_ID = os.environ.get('AZURE_APP_ID', None)
    AZURE_APP_SECRET = os.environ.get('AZURE_APP_SECRET', None)
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID', None)
    SECRET_KEY = AZURE_APP_SECRET
    if AZURE_TENANT_ID is None:
        raise EnvironmentError('AZURE_TENANT_ID is not set')
    if AZURE_APP_ID is None:
        raise EnvironmentError('AZURE_APP_ID is not set')
    if AZURE_APP_SECRET is None:
        raise EnvironmentError('AZURE_APP_SECRET is not set')


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