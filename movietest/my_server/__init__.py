from flask import Flask
app = Flask(__name__)
from my_server import routes, errors
from my_server.config import Config

app.config.from_object(Config)


