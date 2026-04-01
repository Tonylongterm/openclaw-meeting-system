from flask import Flask, request, jsonify, Response, g, send_from_directory
from flask_cors import CORS
import json
import uuid
import queue
import time
import jwt
import os
import random
import string
from functools import wraps
from agents import ParticipantAgent
from meeting_system import MeetingRoom

app = Flask(__name__)
CORS(app)

SECRET_KEY = "openclaw-meeting-secret-2024"

# In-memory storage
users = {}  # email -> {email, password, name}
meetings = {}  # meeting_id -> Meeting Object
invite_to_meeting = {}  # invite_code -> meeting_id
msg_queues = {}  # meeting_id -> list of queues

def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.current_user = users.get(data['email'])
            if not g.current_user:
                return jsonify({'message': 'Invalid User!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({"message": "Missing fields"}), 400
    
    if email in users:
        return jsonify({"message": "User already exists"}), 400
        
    users[email] = {"email": email, "password": password, "name": name}
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = users.get(email)
    if not user or user['password'] != password:
        return jsonify({"message": "Invalid credentials"}), 401
        
    token = jwt.encode({'email': email, 'exp': time.time() + 86400}, SECRET_KEY, algorithm="HS256")
    return jsonify({
        "token": token,
        "user": {"email": user['email'], "name": user['name']}
    })

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me():
    return jsonify(g.current_user)

# Meeting Management
@app.route('/api/meetings', methods=['POST'])
@token_required
def create_meeting():
    data = request.json
    title = data.get('title')
    topic = data.get('topic')
    max_rounds = int(data.get('max_rounds', 5))
    
    meeting_id = str(uuid.uuid4())
    invite_code = generate_invite_code()
    while invite_code in invite_to_meeting:
        invite_code = generate_invite_code()
        
    room = MeetingRoom(meeting_id, title, topic, max_rounds)
    room.invite_code = invite_code
    room.owner_email = g.current_user['email']
    room.created_at = time.time()
    
    def broadcast_to_queues(msg):
        if meeting_id in msg_queues:
            for q in msg_queues[meeting_id]:
                q.put(msg)
    
    room.add_callback(broadcast_to_queues)
    
    meetings[meeting_id] = room
    invite_to_meeting[invite_code] = meeting_id
    
    return jsonify({
        "success": True,
        "meeting": {
            "id": meeting_id,
            "title": title,
            "topic": topic,
            "max_rounds": max_rounds,
            "invite_code": invite_code,
            "status": room.status
        }
    })

@app.route('/api/meetings', methods=['GET'])
@token_required
def list_meetings():
    user_meetings = []
    for m_id, m in meetings.items():
        if m.owner_email == g.current_user['email']:
            user_meetings.append({
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "invite_code": m.invite_code,
                "agent_count": len(m.agents),
                "created_at": m.created_at
            })
    user_meetings.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(user_meetings)

@app.route('/api/meetings/<meeting_id>', methods=['GET'])
@token_required
def get_meeting(meeting_id):
    m = meetings.get(meeting_id)
    if not m:
        return jsonify({"message": "Meeting not found"}), 404
    
    if m.owner_email != g.current_user['email']:
        return jsonify({"message": "Access denied"}), 403
        
    return jsonify({
        "id": m.id,
        "title": m.title,
        "topic": m.topic,
        "max_rounds": m.max_rounds,
        "invite_code": m.invite_code,
        "status": m.status,
        "agents": [{"name": a.name, "role": a.role, "description": a.description} for a in m.agents],
        "host_agent": m.moderator.name if m.moderator else None,
        "current_round": m.current_round,
        "end_reason": m.end_reason
    })

@app.route('/api/meetings/<meeting_id>', methods=['PATCH'])
@token_required
def update_meeting(meeting_id):
    m = meetings.get(meeting_id)
    if not m or m.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403
        
    data = request.json
    if 'title' in data: m.title = data['title']
    if 'topic' in data: m.topic = data['topic']
    if 'max_rounds' in data: m.max_rounds = int(data['max_rounds'])
    if 'host_agent' in data: m.set_moderator(data['host_agent'])
    
    return jsonify({"success": True})

@app.route('/api/meetings/<meeting_id>', methods=['DELETE'])
@token_required
def delete_meeting(meeting_id):
    m = meetings.get(meeting_id)
    if not m or m.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403
        
    del invite_to_meeting[m.invite_code]
    del meetings[meeting_id]
    if meeting_id in msg_queues:
        del msg_queues[meeting_id]
        
    return jsonify({"success": True})

@app.route('/api/meetings/<meeting_id>/start', methods=['POST'])
@token_required
def start_meeting(meeting_id):
    m = meetings.get(meeting_id)
    if not m or m.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403
        
    if not m.moderator:
        return jsonify({"success": False, "message": "Host agent not set"}), 400
        
    m.start_in_background()
    return jsonify({"success": True})

@app.route('/api/meetings/<meeting_id>/status', methods=['GET'])
def get_meeting_status(meeting_id):
    m = meetings.get(meeting_id)
    if not m: return jsonify({"message": "Not found"}), 404
    return jsonify({
        "id": m.id,
        "status": m.status,
        "current_round": m.current_round,
        "max_rounds": m.max_rounds,
        "end_reason": m.end_reason,
        "agent_count": len(m.agents)
    })

@app.route('/api/meetings/<meeting_id>/stream')
def stream_meeting(meeting_id):
    if meeting_id not in meetings:
        return jsonify({"message": "Not found"}), 404
        
    def event_stream():
        q = queue.Queue()
        if meeting_id not in msg_queues:
            msg_queues[meeting_id] = []
        msg_queues[meeting_id].append(q)
        
        # Send history
        m = meetings[meeting_id]
        # Current state
        yield f"data: {json.dumps({'type': 'init', 'status': m.status, 'topic': m.topic})}\n\n"
        
        try:
            while True:
                msg = q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except GeneratorExit:
            if meeting_id in msg_queues:
                msg_queues[meeting_id].remove(q)
                
    return Response(event_stream(), mimetype="text/event-stream")

# Lobster Join API
@app.route('/api/join', methods=['POST'])
def join_meeting():
    data = request.json
    invite_code = data.get('invite_code')
    name = data.get('name')
    role = data.get('role')
    desc = data.get('description', '')
    
    m_id = invite_to_meeting.get(invite_code)
    if not m_id:
        return jsonify({"success": False, "message": "Invalid invite code"}), 404
        
    m = meetings[m_id]
    agent = ParticipantAgent(name, role, desc)
    if m.register_agent(agent):
        return jsonify({
            "success": True,
            "meeting_id": m.id,
            "meeting_title": m.title,
            "agent_id": str(uuid.uuid4())
        })
    else:
        return jsonify({"success": False, "message": "Name already taken"}), 400

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/app')
def app_page():
    return send_from_directory('static', 'app.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7788))
    print(f"Starting V3 Meeting Server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
