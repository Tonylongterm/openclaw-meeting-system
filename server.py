from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import uuid
import queue
import time
from agents import ParticipantAgent
from meeting_system import MeetingEngine

app = Flask(__name__)
CORS(app)

# Global Meeting Engine and Message Queue
engine = None
msg_queue = queue.Queue()

# Store registered agents in memory for retrieval
registered_agents = []

def broadcast_to_sse(message):
    msg_queue.put(message)

@app.route('/api/agents/register', methods=['POST'])
def register_agent():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    description = data.get('description', '')
    
    if not name or not role:
        return jsonify({"success": False, "message": "Missing name or role"}), 400
    
    agent = ParticipantAgent(name, role, description)
    
    # We need a temporary engine if not created yet, or use the global one
    global engine
    if engine:
        success = engine.register_agent(agent)
    else:
        # Check for duplicate in registered_agents list
        if any(a['name'] == name for a in registered_agents):
            success = False
        else:
            registered_agents.append({
                "name": name,
                "role": role,
                "description": description,
                "agent_id": str(uuid.uuid4())
            })
            success = True
            
    if success:
        # If engine was already running, we might want to notify via SSE
        broadcast_to_sse({"type": "agent_registered", "name": name, "role": role})
        return jsonify({
            "success": True, 
            "agent_id": str(uuid.uuid4()), 
            "message": "注册成功"
        })
    else:
        return jsonify({"success": False, "message": "Agent name already exists"}), 400

@app.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    global engine, registered_agents
    data = request.json
    topic = data.get('topic', 'Untitled Meeting')
    max_rounds = data.get('max_rounds', 5)
    
    engine = MeetingEngine(topic=topic, max_rounds=max_rounds)
    engine.add_callback(broadcast_to_sse)
    
    # Re-register existing agents if any
    for a in registered_agents:
        engine.register_agent(ParticipantAgent(a['name'], a['role'], a['description']))
        
    return jsonify({"success": True, "meeting_id": str(uuid.uuid4())})

@app.route('/api/meeting/set_host', methods=['POST'])
def set_host():
    global engine
    if not engine:
        return jsonify({"success": False, "message": "Meeting not created"}), 400
    
    data = request.json
    agent_name = data.get('agent_name')
    if engine.set_moderator(agent_name):
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Agent not found"}), 404

@app.route('/api/meeting/start', methods=['POST'])
def start_meeting():
    global engine
    if not engine:
        return jsonify({"success": False, "message": "Meeting not created"}), 400
    if not engine.moderator:
        return jsonify({"success": False, "message": "Moderator not set"}), 400
    
    engine.start_in_background()
    return jsonify({"success": True, "message": "会议已开始"})

@app.route('/api/meeting/status', methods=['GET'])
def get_status():
    global engine, registered_agents
    if not engine:
        return jsonify({
            "status": "not_created",
            "agents": registered_agents
        })
    
    return jsonify({
        "topic": engine.topic,
        "status": engine.status,
        "current_round": engine.current_round,
        "max_rounds": engine.max_rounds,
        "is_finished": engine.status == "finished",
        "end_reason": engine.end_reason,
        "agents": [{"name": a.name, "role": a.role} for a in engine.agents],
        "moderator": engine.moderator.name if engine.moderator else None
    })

@app.route('/api/meeting/stream')
def stream():
    def event_stream():
        # Optional: Send current state first
        while True:
            try:
                msg = msg_queue.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                # Keep alive
                yield ": keep-alive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("Starting Meeting Server on 0.0.0.0:7788")
    app.run(host='0.0.0.0', port=7788, threaded=True)
