#!flask/bin/python
from flask import Flask

try:
    from local_config import LocalConfig as Config
except ImportError:
    from config import Config
    print('No config overrides set, you may need to configure minid and aws.')

app = Flask(__name__)
app.config.from_object(Config)

from api import views

