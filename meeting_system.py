import time
import threading
from agents import ModeratorAgent, ParticipantAgent

class MeetingRoom:
    def __init__(self, meeting_id, title, topic, max_rounds=5):
        self.id = meeting_id
        self.title = title
        self.topic = topic
        self.max_rounds = max_rounds
        self.agents = []
        self.moderator = None
        self.records = []
        self.consensus_keywords = ["同意", "agree", "共识", "consensus", "赞成"]
        self.status = "waiting" # waiting, running, finished
        self.current_round = 0
        self.end_reason = ""
        self.callbacks = []
        self._lock = threading.Lock()

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def _broadcast(self, msg_type, **kwargs):
        message = {"type": msg_type, **kwargs}
        for cb in self.callbacks:
            try:
                cb(message)
            except:
                pass

    def register_agent(self, agent):
        with self._lock:
            if any(a.name == agent.name for a in self.agents):
                return False
            self.agents.append(agent)
            self._broadcast("agent_registered", name=agent.name, role=agent.role)
            return True

    def set_moderator(self, agent_name):
        with self._lock:
            for agent in self.agents:
                if agent.name == agent_name:
                    self.moderator = ModeratorAgent(agent.name, agent.role, agent.description)
                    return True
            return False

    def check_consensus(self, speech):
        for keyword in self.consensus_keywords:
            if keyword in speech:
                return True
        return False

    def run_meeting(self):
        if not self.moderator:
            return

        self.status = "running"
        self.current_round = 0
        
        intro_text = self.moderator.introduce(self.topic)
        self._broadcast("speech", agent=self.moderator.name, role="主持人", content=intro_text, round=0)
        time.sleep(1)

        reached_consensus = False
        final_round = 0

        for r in range(1, self.max_rounds + 1):
            self.current_round = r
            self._broadcast("round_start", round=r)
            round_records = []
            consensus_this_round = 0

            for agent in self.agents:
                if self.moderator and agent.name == self.moderator.name:
                    continue
                
                speech = agent.speak(self.topic, r, round_records)
                is_consensus = self.check_consensus(speech)
                if is_consensus:
                    consensus_this_round += 1
                
                self._broadcast("speech", agent=agent.name, role=agent.role, content=speech, round=r)
                
                record = {
                    "round": r,
                    "agent": agent.name,
                    "role": agent.role,
                    "speech": speech,
                    "consensus": is_consensus
                }
                round_records.append(record)
                self.records.append(record)
                time.sleep(1)

            self._broadcast("round_end", round=r)
            
            participant_count = len(self.agents) - (1 if self.moderator else 0)
            if participant_count > 0 and consensus_this_round >= participant_count:
                reached_consensus = True
                final_round = r
                break
            
            if r < self.max_rounds:
                wrap_text = self.moderator.wrap_round(r)
                self._broadcast("speech", agent=self.moderator.name, role="主持人", content=wrap_text, round=r)
            
            final_round = r
            time.sleep(0.5)

        if reached_consensus:
            self.end_reason = "所有参与者达成共识"
        else:
            self.end_reason = f"达到最大轮数限制 ({self.max_rounds} 轮)"
        
        conclude_text = self.moderator.conclude(self.end_reason)
        self._broadcast("speech", agent=self.moderator.name, role="主持人", content=conclude_text, round=final_round)
        
        self.status = "finished"
        self._broadcast("meeting_end", reason=self.end_reason)

    def start_in_background(self):
        thread = threading.Thread(target=self.run_meeting)
        thread.daemon = True
        thread.start()
        return thread
