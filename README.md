# OpenClaw 多 Agent 会议系统

这是一个演示多 Agent 协同会议的简化原型系统。

## 功能特点

1. **Agent 注册**：支持动态注册 Agent 实体，包含名称、角色和描述。
2. **主持人机制**：可指定已注册的某个 Agent 担任会议主持人，负责引导演进。
3. **多轮讨论**：在每一轮会议中，每位 Agent 都会根据会议主题进行发言。
4. **共识判断**：系统会自动分析每位 Agent 的发言内容，识别是否达成共识（关键词匹配：同意、赞成、共识等）。
5. **会议终止条件**：当达到最大轮数限制，或所有参与者均达成共识时，会议自动结束。
6. **会议总结**：会议结束后生成简明扼要的会议纪要。

## 目录结构

- `meeting_system.py`：核心会议调度引擎及共识逻辑。
- `agents.py`：Agent 基类与不同角色的定义，包含 Mock 发言生成。
- `main.py`：项目入口，用于运行完整的演示场景。

## 快速开始

```bash
cd /home/ecs-user/.openclaw/workspace/projects/openclaw-meeting-system
python main.py
```
