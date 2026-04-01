import random

class BaseAgent:
    def __init__(self, name, role, description):
        self.name = name
        self.role = role
        self.description = description
        self.consensus_reached = False

    def speak(self, topic, round_num, context):
        """
        Mock LLM 发言生成逻辑
        """
        templates = [
            f"我认为关于'{topic}'，我们应该更多地关注实际落地。作为{self.role}，我的建议是加强协作。",
            f"从{self.role}的角度看，当前的讨论非常有价值。我支持之前的观点。",
            f"对于第{round_num}轮的讨论，我提出一个新的视角：我们需要考虑长期的可持续性。",
            f"我对此表示赞成，大家达成了共识。",
            f"这个提议听起来不错，我同意这个方向。",
            f"我认为我们还需要再讨论一下细节，但我基本赞同大家的意见。",
            f"同意。我们可以按照这个方案执行。"
        ]
        
        # 模拟随着轮次增加，达成共识的概率增加
        if round_num > 1 and random.random() > 0.6:
            speech = random.choice([
                "我完全同意目前的方案，达成共识。",
                "赞成！这个决定很明智。",
                "我没有异议，达成共识。",
                "好的，我同意大家的看法。"
            ])
        else:
            speech = random.choice(templates[:3])
            
        return speech

class ParticipantAgent(BaseAgent):
    def __init__(self, name, role, description):
        super().__init__(name, role, description)

class ModeratorAgent(BaseAgent):
    def __init__(self, name, role, description):
        super().__init__(name, role, description)

    def introduce(self, topic):
        return f"【主持人 {self.name}】: 各位好，欢迎参加本次会议。今天我们的主题是：'{topic}'。请大家踊跃发言。"

    def wrap_round(self, round_num):
        return f"【主持人 {self.name}】: 第 {round_num} 轮讨论结束。感谢各位的发言。接下来进入下一阶段。"

    def conclude(self, reason):
        return f"【主持人 {self.name}】: 会议结束。原因：{reason}。感谢大家的参与！"
