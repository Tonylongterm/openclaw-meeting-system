from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({"message": "Vercel Mock OK"}), 201

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "Vercel Deployment Alive"
