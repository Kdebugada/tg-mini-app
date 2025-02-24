from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=443,
        ssl_context=('cert.pem', 'key.pem'),
        debug=True
    ) 