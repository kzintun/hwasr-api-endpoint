from flask import Flask
from flask_cors import CORS, cross_origin

UPLOAD_FOLDER = '/local/api-endpoint/files'

app = Flask(__name__)
CORS(app, support_credentials=True)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
