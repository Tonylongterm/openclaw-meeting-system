from agents import ParticipantAgent
from meeting_system import MeetingEngine

def main():
    # 创建会议引擎
    meeting_topic = "OpenClaw 系统的未来架构演进与优化"
    engine = MeetingEngine(topic=meeting_topic, max_rounds=3)

    # 注册 Agent
    agent1 = ParticipantAgent(name="Alice", role="产品经理", description="关注用户体验和需求落地")
    agent2 = ParticipantAgent(name="Bob", role="系统架构师", description="关注系统稳定性和可扩展性")
    agent3 = ParticipantAgent(name="Charlie", role="前端工程师", description="关注界面美观和性能")

    engine.register_agent(agent1)
    engine.register_agent(agent2)
    engine.register_agent(agent3)

    # 设定主持人
    engine.set_moderator("Alice")

    # 开始会议
    engine.run_meeting()

if __name__ == "__main__":
    main()
