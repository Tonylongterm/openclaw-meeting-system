import os
import subprocess
import time

PROJECT_DIR = "/home/ecs-user/.openclaw/workspace/projects/openclaw-meeting-system"
EVIDENCE_PATH = os.path.join(PROJECT_DIR, "tests/evidence_register.png")

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def audit():
    print(f"\n--- [{time.ctime()}] 研发总监智能审计启动 ---")
    
    # 1. 检查最新提交
    last_commit = run_cmd(f"cd {PROJECT_DIR} && git log -1 --oneline")
    print(f"[Git状态] 最新提交: {last_commit}")
    
    # 2. 检查视觉证据 (截图)
    if not os.path.exists(EVIDENCE_PATH):
        print("[报警] ❌ 严重失职：未发现浏览器测试截图证据！Codex 正在盲目开发。")
    else:
        mtime = os.path.getmtime(EVIDENCE_PATH)
        if (time.time() - mtime) > 600:
            print("[报警] ⚠️ 证据过期：截图证据已超过 10 分钟未更新，测试已停滞。")
        else:
            print("[合规] ✅ 发现最新截图证据。")

    # 3. 检查自检脚本运行情况
    qa_report = run_cmd(f"cd {PROJECT_DIR} && python3 tests/qa_check.py 2>&1")
    if "PASSED" in qa_report:
        print("[合规] ✅ 自动化回归测试通过。")
    else:
        print(f"[报警] ❌ 回归测试失败！输出摘要: {qa_report[:100]}...")

    # 4. 信心指数挑战
    # 模拟检查 Codex 的承诺日志
    print("[指令] Codex 必须在下一次审计前提交包含 'Evidence Found' 的视觉分析报告。")

if __name__ == "__main__":
    audit()
