print('--- RELOADED SERVER V5 (STATIC HTML FILES) ---')

import json
import os
import queue
import random
import string
import time
import uuid
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, Response, g, jsonify, request
from flask_cors import CORS

from agents import ParticipantAgent
from meeting_system import MeetingRoom

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'


def resolve_static_dir():
    static_exists = STATIC_DIR.is_dir()
    print(
        f"[startup] cwd={Path.cwd()} base_dir={BASE_DIR} "
        f"static_dir={STATIC_DIR} exists={static_exists}"
    )

    if static_exists:
        return STATIC_DIR

    candidate_dirs = [
        STATIC_DIR,
        Path.cwd() / 'static',
        BASE_DIR / 'static',
        BASE_DIR.parent / 'static',
    ]

    for candidate in candidate_dirs:
        if candidate.is_dir():
            print(f"[startup] static directory repaired: {candidate}")
            return candidate

    print("[startup] static directory not found in expected locations")
    return STATIC_DIR


STATIC_DIR = resolve_static_dir()

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='/static')
CORS(app)

SECRET_KEY = "openclaw-meeting-secret-2024"

HTML_FILES = {
    "index": STATIC_DIR / "index.html",
    "auth": STATIC_DIR / "auth.html",
    "app": STATIC_DIR / "app.html",
}


def render_html_page(page_name):
    html_path = HTML_FILES[page_name]
    html = html_path.read_text(encoding="utf-8")
    return Response(html, mimetype="text/html; charset=utf-8")


# In-memory storage
users = {}  # email -> {email, password, name}
meetings = {}  # meeting_id -> Meeting Object
invite_to_meeting = {}  # invite_code -> meeting_id
msg_queues = {}  # meeting_id -> list of queues


def build_tree(path, max_depth=2, max_entries=50):
    tree = {
        "name": path.name or str(path),
        "path": str(path),
        "type": "dir" if path.is_dir() else "file",
    }
    if not path.is_dir():
        return tree

    if max_depth <= 0:
        tree["children"] = ["... depth limit reached ..."]
        return tree

    try:
        entries = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    except Exception as exc:
        tree["error"] = str(exc)
        return tree

    children = []
    for index, entry in enumerate(entries):
        if index >= max_entries:
            children.append({"name": "... truncated ...", "path": str(path), "type": "meta"})
            break
        children.append(build_tree(entry, max_depth=max_depth - 1, max_entries=max_entries))
    tree["children"] = children
    return tree


def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def get_request_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]
    query_token = request.args.get('token')
    if query_token:
        return query_token
    return request.cookies.get('token')


def has_valid_request_token():
    token = get_request_token()
    if not token:
        return False

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return False

    return data.get('email') in users


def resolve_current_user():
    token = get_request_token()
    if not token:
        return None, (jsonify({'message': 'Token is missing!'}), 401)

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        current_user = users.get(data['email'])
        if not current_user:
            return None, (jsonify({'message': 'Invalid User!'}), 401)
        return current_user, None
    except Exception as exc:
        return None, (jsonify({'message': 'Token is invalid!', 'error': str(exc)}), 401)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user, error_response = resolve_current_user()
        if error_response:
            return error_response

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
    response = jsonify({
        "token": token,
        "user": {"email": user['email'], "name": user['name']}
    })
    response.set_cookie('token', token, max_age=86400, samesite='Lax', path='/')
    return response


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me():
    return jsonify(g.current_user)


@app.route('/api/meetings', methods=['POST'])
@token_required
def create_meeting():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    topic = (data.get('topic') or '').strip()

    if not title or not topic:
        return jsonify({"success": False, "message": "Missing required fields: title and topic"}), 400

    try:
        max_rounds = int(data.get('max_rounds', 5))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "max_rounds must be an integer"}), 400

    if max_rounds < 1:
        return jsonify({"success": False, "message": "max_rounds must be greater than 0"}), 400

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
    for m_id, meeting in meetings.items():
        if meeting.owner_email == g.current_user['email']:
            user_meetings.append({
                "id": m_id,
                "title": meeting.title,
                "status": meeting.status,
                "invite_code": meeting.invite_code,
                "agent_count": len(meeting.agents),
                "created_at": meeting.created_at
            })
    user_meetings.sort(key=lambda item: item['created_at'], reverse=True)
    return jsonify(user_meetings)


@app.route('/api/meetings/<meeting_id>', methods=['GET'])
@token_required
def get_meeting(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting:
        return jsonify({"message": "Meeting not found"}), 404

    if meeting.owner_email != g.current_user['email']:
        return jsonify({"message": "Access denied"}), 403

    return jsonify({
        "id": meeting.id,
        "title": meeting.title,
        "topic": meeting.topic,
        "max_rounds": meeting.max_rounds,
        "invite_code": meeting.invite_code,
        "status": meeting.status,
        "agents": [{"name": a.name, "role": a.role, "description": a.description} for a in meeting.agents],
        "host_agent": meeting.moderator.name if meeting.moderator else None,
        "current_round": meeting.current_round,
        "end_reason": meeting.end_reason
    })


@app.route('/api/meetings/<meeting_id>', methods=['PATCH'])
@token_required
def update_meeting(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting or meeting.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403

    data = request.json
    if 'title' in data:
        meeting.title = data['title']
    if 'topic' in data:
        meeting.topic = data['topic']
    if 'max_rounds' in data:
        meeting.max_rounds = int(data['max_rounds'])
    if 'host_agent' in data:
        meeting.set_moderator(data['host_agent'])

    return jsonify({"success": True})


@app.route('/api/meetings/<meeting_id>', methods=['DELETE'])
@token_required
def delete_meeting(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting or meeting.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403

    del invite_to_meeting[meeting.invite_code]
    del meetings[meeting_id]
    if meeting_id in msg_queues:
        del msg_queues[meeting_id]

    return jsonify({"success": True})


@app.route('/api/meetings/<meeting_id>/start', methods=['POST'])
@token_required
def start_meeting(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting or meeting.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403

    if not meeting.moderator:
        return jsonify({"success": False, "message": "Host agent not set"}), 400

    meeting.start_in_background()
    return jsonify({"success": True})


@app.route('/api/meetings/<meeting_id>/status', methods=['GET'])
def get_meeting_status(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting:
        return jsonify({"message": "Not found"}), 404
    return jsonify({
        "id": meeting.id,
        "status": meeting.status,
        "current_round": meeting.current_round,
        "max_rounds": meeting.max_rounds,
        "end_reason": meeting.end_reason,
        "agent_count": len(meeting.agents)
    })


@app.route('/api/meetings/<meeting_id>/stream')
def stream_meeting(meeting_id):
    current_user, error_response = resolve_current_user()
    if error_response:
        return error_response

    meeting = meetings.get(meeting_id)
    if not meeting:
        return jsonify({"message": "Not found"}), 404
    if meeting.owner_email != current_user['email']:
        return jsonify({"message": "Access denied"}), 403

    def event_stream():
        q = queue.Queue()
        if meeting_id not in msg_queues:
            msg_queues[meeting_id] = []
        msg_queues[meeting_id].append(q)

        yield f"data: {json.dumps({'type': 'init', 'status': meeting.status, 'topic': meeting.topic})}\n\n"

        try:
            while True:
                msg = q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except GeneratorExit:
            if meeting_id in msg_queues and q in msg_queues[meeting_id]:
                msg_queues[meeting_id].remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/api/join', methods=['POST'])
def join_meeting():
    data = request.json
    invite_code = data.get('invite_code')
    name = data.get('name')
    role = data.get('role')
    desc = data.get('description', '')

    meeting_id = invite_to_meeting.get(invite_code)
    if not meeting_id:
        return jsonify({"success": False, "message": "Invalid invite code"}), 404

    meeting = meetings[meeting_id]
    agent = ParticipantAgent(name, role, desc)
    if meeting.register_agent(agent):
        return jsonify({
            "success": True,
            "meeting_id": meeting.id,
            "meeting_title": meeting.title,
            "agent_id": str(uuid.uuid4())
        })
    return jsonify({"success": False, "message": "Name already taken"}), 400


def health_payload():
    static_root = Path(app.static_folder).resolve()
    return {
        "status": "ok",
        "cwd": str(Path.cwd()),
        "base_dir": str(BASE_DIR),
        "static_folder": str(static_root),
        "static_exists": static_root.is_dir(),
        "index_exists": (static_root / 'index.html').is_file(),
        "auth_exists": (static_root / 'auth.html').is_file(),
        "app_exists": (static_root / 'app.html').is_file(),
    }


@app.route('/api/health', methods=['GET'])
@app.route('/api/meeting/status', methods=['GET'])
def healthcheck():
    return jsonify(health_payload())


@app.route('/debug/ls', methods=['GET'])
def debug_ls():
    current_path = Path.cwd().resolve()
    parents = [current_path, *current_path.parents]
    return jsonify({
        "cwd": str(current_path),
        "base_dir": str(BASE_DIR),
        "static_folder": str(Path(app.static_folder).resolve()),
        "levels": [build_tree(path, max_depth=2, max_entries=50) for path in parents],
    })


@app.route('/')
def index():
    return render_html_page("index")


@app.route('/app')
def app_page():
    auth_mode = request.args.get('auth')
    if auth_mode in {'login', 'register'}:
        return render_html_page("auth")
    if not has_valid_request_token():
        return render_html_page("auth")
    return render_html_page("app")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7788))
    print(f"Starting V5 Meeting Server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
