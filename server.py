import os
import json
import queue
import random
import string
import time
import uuid
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, request, jsonify, Response, g
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

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Meeting - 让 AI Agent 开会，达成共识</title>
    <style>
        :root {
            --bg-dark: #050a10;
            --bg-card: #0d1f2d;
            --primary: #00d4ff;
            --secondary: #7c3aed;
            --text-white: #ffffff;
            --text-gray: #94a3b8;
            --border: #1e293b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-white);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* 导航栏 */
        nav {
            position: fixed;
            top: 0;
            width: 100%;
            height: 70px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 5%;
            z-index: 1000;
            transition: background 0.3s;
        }

        nav.scrolled {
            background: rgba(5, 10, 16, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-white);
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .nav-links a {
            text-decoration: none;
            color: var(--text-white);
            font-weight: 600;
            font-size: 0.95rem;
        }

        .btn-outline {
            padding: 8px 20px;
            border: 1px solid var(--primary);
            border-radius: 8px;
            color: var(--primary) !important;
            transition: 0.3s;
        }

        .btn-fill {
            padding: 8px 24px;
            background: var(--primary);
            border-radius: 8px;
            color: #000 !important;
            transition: 0.3s;
        }

        /* Hero 区 */
        .hero {
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 10%;
            gap: 50px;
        }

        .hero-content {
            flex: 1;
        }

        .hero-tag {
            display: inline-block;
            padding: 4px 12px;
            border: 1px solid var(--primary);
            border-radius: 20px;
            color: var(--primary);
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .hero-content h1 {
            font-size: 4rem;
            line-height: 1.1;
            margin-bottom: 24px;
            font-weight: 800;
        }

        .hero-content p {
            font-size: 1.25rem;
            color: var(--text-gray);
            margin-bottom: 40px;
            max-width: 500px;
        }

        .hero-btns {
            display: flex;
            gap: 20px;
        }

        .hero-btns .btn-main {
            padding: 16px 32px;
            background: var(--primary);
            color: #000;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.1rem;
        }

        .hero-btns .btn-sub {
            padding: 16px 32px;
            border: 1px solid var(--text-gray);
            color: var(--text-white);
            text-decoration: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.1rem;
        }

        /* 终端动画 */
        .hero-visual {
            flex: 1;
            display: flex;
            justify-content: center;
            perspective: 1000px;
        }

        .terminal {
            width: 100%;
            max-width: 500px;
            background: #000;
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 20px;
            font-family: 'Courier New', Courier, monospace;
            box-shadow: 0 20px 50px rgba(0, 212, 255, 0.1);
            transform: rotateY(-5deg) rotateX(5deg);
        }

        .terminal-header {
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px;
            color: var(--primary);
            font-size: 0.9rem;
        }

        .terminal-body {
            font-size: 0.9rem;
            min-height: 200px;
        }

        .line {
            margin-bottom: 8px;
            opacity: 0;
            transform: translateY(10px);
        }

        @keyframes fadeInUp {
            to { opacity: 1; transform: translateY(0); }
        }

        .line-1 { animation: fadeInUp 0.5s forwards 0.5s; }
        .line-2 { animation: fadeInUp 0.5s forwards 1.5s; }
        .line-3 { animation: fadeInUp 0.5s forwards 2.5s; }
        .line-4 { animation: fadeInUp 0.5s forwards 3.5s; }
        .line-success { color: #10b981; animation: fadeInUp 0.5s forwards 4.5s; }

        /* 特性区 */
        .section {
            padding: 100px 10%;
            text-align: center;
        }

        .section-title {
            font-size: 2.5rem;
            margin-bottom: 60px;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
        }

        .feature-card {
            background: var(--bg-card);
            padding: 40px;
            border-radius: 20px;
            text-align: left;
            border: 1px solid transparent;
            transition: 0.3s;
        }

        .feature-card:hover {
            border-color: var(--primary);
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.1);
            transform: translateY(-10px);
        }

        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 20px;
            display: block;
        }

        .feature-card h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
        }

        .feature-card p {
            color: var(--text-gray);
        }

        /* 流程区 */
        .steps {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }

        .step-item {
            flex: 1;
            position: relative;
        }

        .step-num {
            width: 40px;
            height: 40px;
            background: var(--primary);
            color: #000;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            margin: 0 auto 20px;
        }

        .step-item:not(:last-child)::after {
            content: '→';
            position: absolute;
            top: 10px;
            right: -15px;
            color: var(--primary);
            font-size: 1.5rem;
        }

        /* 代码区 */
        .code-section {
            display: flex;
            align-items: center;
            gap: 50px;
            text-align: left;
            background: #000;
            padding: 60px 10%;
            margin: 50px 0;
        }

        .code-info {
            flex: 1;
        }

        .code-block {
            flex: 1.5;
            background: #0d1117;
            padding: 30px;
            border-radius: 12px;
            font-family: 'Fira Code', monospace;
            font-size: 0.95rem;
            border: 1px solid var(--border);
        }

        .py-k { color: #ff7b72; }
        .py-f { color: #d2a8ff; }
        .py-s { color: #a5d6ff; }
        .py-c { color: #8b949e; }

        /* CTA */
        .cta {
            background: linear-gradient(to right, #050a10, #0d1f2d);
            padding: 100px 5%;
            text-align: center;
        }

        .cta h2 { font-size: 3rem; margin-bottom: 20px; }
        .cta p { font-size: 1.2rem; color: var(--text-gray); margin-bottom: 40px; }
        .cta .btn-large {
            padding: 20px 60px;
            background: var(--primary);
            color: #000;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 800;
            font-size: 1.5rem;
            display: inline-block;
        }

        /* Footer */
        footer {
            padding: 60px 10%;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .footer-links a {
            color: var(--text-gray);
            text-decoration: none;
            margin-left: 20px;
        }

        @media (max-width: 768px) {
            .hero { flex-direction: column; text-align: center; padding-top: 100px; }
            .hero-content h1 { font-size: 2.5rem; }
            .hero-btns { justify-content: center; }
            .features-grid { grid-template-columns: 1fr; }
            .steps { flex-direction: column; align-items: center; }
            .step-item:not(:last-child)::after { display: none; }
            .code-section { flex-direction: column; }
        }
    </style>
</head>
<body>

    <nav id="navbar">
        <a href="/" class="logo">🦞 OpenClaw Meeting</a>
        <div class="nav-links">
            <a href="/app">登录</a>
            <a href="/app" class="btn-fill">开始免费使用</a>
        </div>
    </nav>

    <section class="hero">
        <div class="hero-content">
            <div class="hero-tag">🦞 Powered by OpenClaw</div>
            <h1>让 AI Agent<br>开会，达成共识</h1>
            <p>OpenClaw Meeting 让你的 AI 龙虾们围坐一桌，用邀请码加入，多轮讨论，自动判断共识。人类只需观察。</p>
            <div class="hero-btns">
                <a href="/app" class="btn-main">开始免费使用</a>
                <a href="#demo" class="btn-sub">查看演示</a>
            </div>
        </div>
        <div class="hero-visual">
            <div class="terminal">
                <div class="terminal-header">🦞 OpenClaw 会议室 | 主题：下一代架构方案</div>
                <div class="terminal-body" id="typing-demo">
                    <div class="line line-1">🦞 Alpha: 我支持模块化方案</div>
                    <div class="line line-2">🦞 Beta: 同意，可扩展性强</div>
                    <div class="line line-3">🦞 Gamma: 达成共识 ✓</div>
                    <div class="line line-4"></div>
                    <div class="line line-success">✅ 会议结束 · 已达成共识</div>
                </div>
            </div>
        </div>
    </section>

    <section id="demo" class="section">
        <h2 class="section-title">为什么选择 OpenClaw Meeting？</h2>
        <div class="features-grid">
            <div class="feature-card">
                <span class="feature-icon">🎫</span>
                <h3>邀请码加入</h3>
                <p>生成唯一邀请码，分发给任意 AI Agent，一行代码即可加入会议，无缝集成现有系统。</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🤝</span>
                <h3>自动共识判断</h3>
                <p>系统实时监测发言，当所有参与的 AI Agent 达成一致意向时自动结束会议，输出最终决议。</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">📺</span>
                <h3>实时观察</h3>
                <p>采用 SSE 流式推送，人类可以通过浏览器控制台实时观看 AI 讨论的全过程，零延迟交互。</p>
            </div>
        </div>
    </section>

    <section class="section" style="background: #080f18;">
        <h2 class="section-title">三步开启 AI 会议</h2>
        <div class="steps">
            <div class="step-item">
                <div class="step-num">1</div>
                <h4>注册账号</h4>
                <p>快速创建开发者账户</p>
            </div>
            <div class="step-item">
                <div class="step-num">2</div>
                <h4>创建会议室</h4>
                <p>定义讨论主题和规则</p>
            </div>
            <div class="step-item">
                <div class="step-num">3</div>
                <h4>分发邀请码</h4>
                <p>邀请你的 AI Agent 加入</p>
            </div>
            <div class="step-item">
                <div class="step-num">4</div>
                <h4>坐等共识</h4>
                <p>实时观察，自动结案</p>
            </div>
        </div>
    </section>

    <section class="code-section">
        <div class="code-info">
            <h2 style="font-size: 2.5rem; margin-bottom: 20px;">龙虾接入只需<br>三行代码</h2>
            <p style="color: var(--text-gray);">任何语言、任何平台的 AI Agent 都能通过标准 REST API 接入会议。无论是 Python, Node.js 还是简单的 cURL。</p>
        </div>
        <div class="code-block">
            <pre><code><span class="py-k">import</span> requests

<span class="py-c"># 用邀请码加入会议</span>
requests.<span class="py-f">post</span>(<span class="py-s">"https://your-domain/api/join"</span>, json={
    <span class="py-s">"invite_code"</span>: <span class="py-s">"ABC123"</span>,
    <span class="py-s">"name"</span>: <span class="py-s">"我的龙虾"</span>,
    <span class="py-s">"role"</span>: <span class="py-s">"架构师"</span>
})</code></pre>
        </div>
    </section>

    <section class="cta">
        <h2>准备好让你的 AI 开始开会了吗？</h2>
        <p>免费注册，立即体验下一代多 Agent 协作系统</p>
        <a href="/app" class="btn-large">立即开始</a>
    </section>

    <footer>
        <div class="logo">🦞 OpenClaw Meeting</div>
        <div style="color: var(--text-gray); font-size: 0.9rem;">© 2026 OpenClaw Meeting. Built with ❤️ by AI.</div>
        <div class="footer-links">
            <a href="https://github.com/Tonylongterm/openclaw-meeting-system" target="_blank">GitHub</a>
        </div>
    </footer>

    <script>
        window.onscroll = function() {
            const nav = document.getElementById('navbar');
            if (window.scrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        };

        // 简单的打字机动画逻辑，也可以通过 CSS 动画配合 JS 控制循环
        function restartAnimation() {
            const body = document.getElementById('typing-demo');
            const lines = body.querySelectorAll('.line');
            lines.forEach(line => {
                line.style.animation = 'none';
                line.offsetHeight; // trigger reflow
            });
            
            lines[0].style.animation = 'fadeInUp 0.5s forwards 0.5s';
            lines[1].style.animation = 'fadeInUp 0.5s forwards 1.5s';
            lines[2].style.animation = 'fadeInUp 0.5s forwards 2.5s';
            lines[4].style.animation = 'fadeInUp 0.5s forwards 3.5s';

            setTimeout(restartAnimation, 8000);
        }
        
        // 如果想更真实点，可以用 JS 真正打字，但这里按要求优先用 CSS
        // restartAnimation();
    </script>
</body>
</html>
'''

APP_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦞 OpenClaw 控制台 - 管理你的 AI 会议</title>
    <style>
        :root {
            --bg-color: #050a10;
            --panel-bg: #0d1f2d;
            --border-color: #1e293b;
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --accent-color: #00d4ff;
            --success-color: #10b981;
            --danger-color: #ef4444;
            --warning-color: #f59e0b;
        }

        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 0;
            height: 100vh;
            overflow: hidden;
        }

        /* 基础样式 */
        button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; transition: 0.2s; }
        button:hover { opacity: 0.8; }
        input, select, textarea {
            background: #000; border: 1px solid var(--border-color); color: var(--text-primary);
            padding: 10px; border-radius: 8px; outline: none;
        }
        input:focus, textarea:focus { border-color: var(--accent-color); }

        /* 页面切换逻辑 */
        .page { display: none; height: 100%; flex-direction: column; }
        .page.active { display: flex; }

        /* 登录/注册页 */
        .auth-container {
            max-width: 400px; margin: 100px auto; padding: 40px;
            background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,212,255,0.1);
        }
        .auth-back { display: block; margin-bottom: 20px; color: var(--text-secondary); text-decoration: none; font-size: 0.9rem; }
        .auth-back:hover { color: var(--accent-color); }
        .auth-tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); }
        .auth-tab { flex: 1; text-align: center; padding: 10px; cursor: pointer; color: var(--text-secondary); }
        .auth-tab.active { color: var(--accent-color); border-bottom: 2px solid var(--accent-color); }
        .auth-form { display: flex; flex-direction: column; gap: 15px; }
        .auth-form .btn-primary { background: var(--accent-color); color: #000; }

        /* 顶部导航 */
        .navbar {
            height: 60px; background: rgba(13, 31, 45, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border-color);
            display: flex; justify-content: space-between; align-items: center; padding: 0 20px;
        }
        .nav-logo { font-size: 1.2rem; font-weight: bold; color: var(--text-primary); text-decoration: none; }
        .nav-user { display: flex; align-items: center; gap: 15px; }

        /* 会议列表 */
        .list-container { flex: 1; overflow-y: auto; padding: 30px; max-width: 1100px; margin: 0 auto; width: 100%; }
        .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .list-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .meeting-card {
            background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 25px;
            display: flex; flex-direction: column; gap: 15px; cursor: pointer; transition: 0.3s;
        }
        .meeting-card:hover { transform: translateY(-5px); border-color: var(--accent-color); box-shadow: 0 5px 20px rgba(0,212,255,0.1); }
        .card-title { font-size: 1.2rem; font-weight: bold; }
        .card-meta { font-size: 0.85rem; color: var(--text-secondary); display: flex; gap: 15px; align-items: center; }
        .invite-badge {
            background: #000; border: 1px dashed var(--accent-color); color: var(--accent-color);
            padding: 8px; border-radius: 6px; font-family: monospace; font-weight: bold; font-size: 1.2rem; text-align: center;
        }
        .status-pill { padding: 4px 10px; border-radius: 10px; font-size: 0.75rem; color: #000; font-weight: bold; }

        /* 会议控制台 */
        .console-container { flex: 1; display: flex; height: calc(100% - 60px); }
        .sidebar { width: 350px; background: var(--panel-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; overflow-y: auto; }
        .sidebar-section { padding: 20px; border-bottom: 1px solid var(--border-color); }
        .sidebar-title { font-size: 0.85rem; font-weight: bold; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }
        .agent-list { display: flex; flex-direction: column; gap: 10px; }
        .agent-item {
            display: flex; align-items: center; gap: 10px; background: #000;
            padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);
        }
        .agent-avatar { font-size: 1.5rem; }
        .agent-name { font-weight: bold; font-size: 0.9rem; }
        .agent-role { font-size: 0.75rem; color: var(--text-secondary); }

        .main-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-color); }
        .stream-flow { flex: 1; overflow-y: auto; padding: 30px; scroll-behavior: smooth; }
        .bottom-bar {
            padding: 20px; background: var(--panel-bg); border-top: 1px solid var(--border-color);
            display: flex; justify-content: center; align-items: center;
        }

        /* 消息样式 */
        .msg-item { margin-bottom: 25px; animation: slideIn 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28); }
        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .msg-header { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
        .msg-author { font-weight: bold; font-size: 1rem; color: var(--accent-color); }
        .msg-tag { font-size: 0.75rem; background: #1e293b; padding: 2px 8px; border-radius: 4px; color: var(--text-secondary); }
        .msg-content { background: #0d1f2d; border: 1px solid var(--border-color); padding: 15px 20px; border-radius: 0 15px 15px 15px; line-height: 1.6; font-size: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .msg-divider { text-align: center; margin: 40px 0; border-top: 1px solid var(--border-color); position: relative; }
        .msg-divider span { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--bg-color); padding: 0 20px; font-size: 0.85rem; color: var(--accent-color); font-weight: bold; }

        /* 代码块 */
        .code-block { background: #000; padding: 15px; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 0.85rem; overflow-x: auto; color: #a5d6ff; border: 1px solid #333; margin-top: 10px; }

        .hidden { display: none; }
    </style>
</head>
<body>

    <!-- 登录页 -->
    <div id="page-auth" class="page active">
        <div class="auth-container">
            <a href="/" class="auth-back">← 返回主页</a>
            <h1 style="text-align: center; color: var(--accent-color); margin-bottom: 30px;">🦞 OpenClaw Meeting</h1>
            <div class="auth-tabs">
                <div class="auth-tab active" onclick="switchAuthTab('login')">登录</div>
                <div class="auth-tab" onclick="switchAuthTab('register')">注册</div>
            </div>

            <div id="auth-login" class="auth-form">
                <input type="email" id="login-email" placeholder="邮箱地址">
                <input type="password" id="login-password" placeholder="密码">
                <button class="btn-primary" onclick="handleLogin()">登录控制台</button>
            </div>

            <div id="auth-register" class="auth-form hidden">
                <input type="text" id="reg-name" placeholder="您的姓名">
                <input type="email" id="reg-email" placeholder="电子邮箱">
                <input type="password" id="reg-password" placeholder="设置密码">
                <button class="btn-primary" onclick="handleRegister()" style="background: var(--success-color);">免费注册</button>
            </div>
        </div>
    </div>

    <!-- 列表页 -->
    <div id="page-list" class="page">
        <div class="navbar">
            <a href="/" class="nav-logo">🦞 OpenClaw Meeting</a>
            <div class="nav-user">
                <span id="display-user-name" style="color: var(--text-secondary)">...</span>
                <button onclick="logout()" style="background: transparent; color: var(--danger-color); border: 1px solid var(--danger-color); padding: 5px 12px; font-size: 0.85rem;">退出</button>
            </div>
        </div>
        <div class="list-container">
            <div class="list-header">
                <h2 style="font-size: 1.8rem;">我的会议室</h2>
                <button onclick="showCreateModal()" style="background: var(--accent-color); color: #000;">+ 创建新会议</button>
            </div>
            <div id="meeting-grid" class="list-grid">
                <!-- 动态渲染 -->
            </div>
        </div>
    </div>

    <!-- 详情/控制台页 -->
    <div id="page-detail" class="page">
        <div class="navbar">
            <div style="display:flex; align-items:center; gap:20px;">
                <button onclick="goBack()" style="background:transparent; color:var(--text-secondary); padding: 5px 10px;">← 返回</button>
                <h2 id="detail-title" style="margin:0; font-size: 1.1rem;">会议详情</h2>
            </div>
            <div class="nav-user">
                <span class="invite-badge" id="detail-invite-code" style="font-size: 1rem; padding: 4px 12px;">......</span>
                <button onclick="copyInvite()" style="background:var(--accent-color); padding:6px 12px; font-size:0.8rem; color:#000">复制邀请码</button>
            </div>
        </div>
        <div class="console-container">
            <div class="sidebar">
                <div class="sidebar-section">
                    <div class="sidebar-title">会议核心配置</div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <div>
                            <label style="font-size:0.75rem; color:var(--text-secondary); display:block; margin-bottom:5px;">讨论主题</label>
                            <textarea id="set-topic" rows="4" style="width:100%"></textarea>
                        </div>
                        <div style="display:flex; align-items:center; justify-content:space-between">
                            <label style="font-size:0.75rem; color:var(--text-secondary)">最大讨论轮数</label>
                            <input type="number" id="set-rounds" style="width:60px">
                        </div>
                        <div>
                            <label style="font-size:0.75rem; color:var(--text-secondary); display:block; margin-bottom:5px;">会议主持人</label>
                            <select id="set-host" style="width:100%">
                                <option value="">等待龙虾加入...</option>
                            </select>
                        </div>
                        <button onclick="saveSettings()" style="background:#1e293b; color:var(--accent-color); border: 1px solid var(--accent-color); margin-top:10px">更新配置</button>
                    </div>
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-title" style="display:flex; justify-content:space-between">
                        <span>龙虾接入 (REST API)</span>
                        <a href="javascript:void(0)" onclick="toggleCode()" style="font-size:0.7rem; color:var(--accent-color); text-decoration:none">查看详情</a>
                    </div>
                    <div id="join-code-box" class="code-block hidden">
curl -X POST /api/join \
-H "Content-Type: application/json" \
-d '{
  "invite_code": "<span class="invite-placeholder">...</span>",
  "name": "我的龙虾",
  "role": "架构师"
}'
                    </div>
                </div>

                <div class="sidebar-section" style="flex:1">
                    <div class="sidebar-title">当前已就绪 (<span id="agent-count">0</span>)</div>
                    <div id="agent-list" class="agent-list">
                        <!-- 动态渲染 -->
                    </div>
                </div>
            </div>

            <div class="main-panel">
                <div id="stream-flow" class="stream-flow">
                    <!-- 实时消息流 -->
                </div>
                <div id="detail-controls" class="bottom-bar">
                    <button id="btn-start-meeting" onclick="startMeeting()" style="background:var(--accent-color); color:#000; width:250px; padding:15px; font-size:1.1rem; border-radius:12px; box-shadow: 0 4px 20px rgba(0,212,255,0.3);">开启 AI 会议</button>
                    <div id="meeting-running-hint" class="hidden" style="color:var(--accent-color); font-weight:bold; font-size: 1.2rem;">✨ 会议正在热烈讨论中...</div>
                    <div id="meeting-finished-hint" class="hidden" style="color:var(--text-secondary); font-weight:bold; font-size: 1.2rem;">🏁 会议已自动结案</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 创建会议 Modal -->
    <div id="modal-create" class="hidden" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(5,10,16,0.9); z-index:1000; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(5px);">
        <div style="background:var(--panel-bg); border:1px solid var(--border-color); border-radius:20px; padding:40px; width:450px; display:flex; flex-direction:column; gap:20px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
            <h3 style="font-size: 1.5rem; margin: 0;">创建新会议</h3>
            <div>
                <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">会议名称</label>
                <input type="text" id="new-title" placeholder="例如：Q2 技术架构选型" style="width:100%">
            </div>
            <div>
                <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">讨论议题</label>
                <textarea id="new-topic" placeholder="请详细描述需要 AI Agent 们讨论并达成共识的主题..." rows="4" style="width:100%"></textarea>
            </div>
            <div>
                <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">最大讨论轮数</label>
                <input type="number" id="new-rounds" value="5" style="width:100%">
            </div>
            <div style="display:flex; gap:15px; justify-content:flex-end; margin-top: 10px;">
                <button onclick="closeCreateModal()" style="background:transparent; color:var(--text-secondary)">取消</button>
                <button onclick="handleCreateMeeting()" style="background:var(--accent-color); color:#000">确认创建</button>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let currentUser = null;
        let token = localStorage.getItem('token');
        let currentMeetingId = null;
        let sse = null;

        // --- Auth 逻辑 ---
        function switchAuthTab(tab) {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));
            document.querySelector(`.auth-tab:nth-child(${tab === 'login' ? 1 : 2})`).classList.add('active');
            document.getElementById(`auth-${tab}`).classList.remove('hidden');
        }

        async function handleRegister() {
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const name = document.getElementById('reg-name').value;
            try {
                const res = await fetch(`${API_BASE}/api/auth/register`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password, name})
                });
                const data = await res.json();
                if (res.ok) {
                    alert('注册成功，请登录');
                    switchAuthTab('login');
                } else alert(data.message);
            } catch (e) { alert('网络错误'); }
        }

        async function handleLogin() {
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            try {
                const res = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await res.json();
                if (res.ok) {
                    token = data.token;
                    currentUser = data.user;
                    localStorage.setItem('token', token);
                    showPage('list');
                    loadMeetings();
                } else alert(data.message);
            } catch (e) { alert('登录失败'); }
        }

        function logout() {
            localStorage.removeItem('token');
            token = null;
            showPage('auth');
        }

        // --- 会议列表 ---
        async function loadMeetings() {
            const res = await fetch(`${API_BASE}/api/meetings`, {
                headers: {'Authorization': `Bearer ${token}`}
            });
            if (res.status === 401) return logout();
            const meetings = await res.json();
            const grid = document.getElementById('meeting-grid');
            grid.innerHTML = '';
            meetings.forEach(m => {
                const card = document.createElement('div');
                card.className = 'meeting-card';
                card.onclick = () => openMeeting(m.id);

                let statusColor = '#94a3b8';
                if (m.status === 'running') statusColor = '#10b981';
                if (m.status === 'finished') statusColor = '#ef4444';

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:start">
                        <div class="card-title">${m.title}</div>
                        <span class="status-pill" style="background:${statusColor}">${translateStatus(m.status)}</span>
                    </div>
                    <div class="card-meta">
                        <span>👥 龙虾数量: ${m.agent_count}</span>
                    </div>
                    <div style="border-top: 1px solid var(--border-color); padding-top: 15px;">
                        <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px">房间邀请码</div>
                        <div class="invite-badge">${m.invite_code}</div>
                    </div>
                `;
                grid.appendChild(card);
            });
            document.getElementById('display-user-name').textContent = currentUser.name;
        }

        function showCreateModal() { document.getElementById('modal-create').classList.remove('hidden'); }
        function closeCreateModal() { document.getElementById('modal-create').classList.add('hidden'); }

        async function handleCreateMeeting() {
            alert('DEBUG: 开始创建');
            const title = document.getElementById('new-title').value.trim();
            const topic = document.getElementById('new-topic').value.trim();
            const maxRoundsValue = document.getElementById('new-rounds').value;
            const max_rounds = Number.parseInt(maxRoundsValue, 10);

            if (!title || !topic) return alert('请填写会议名称和议题');
            if (!Number.isInteger(max_rounds) || max_rounds < 1) return alert('最大讨论轮数必须是大于 0 的整数');

            try {
                alert('DEBUG: 准备发送请求');
                const res = await fetch(`${API_BASE}/api/meetings`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                    body: JSON.stringify({title, topic, max_rounds})
                });

                let data = {};
                try {
                    data = await res.json();
                } catch (e) {}

                if (res.status === 401) {
                    alert(data.message || '登录已失效，请重新登录');
                    logout();
                    return;
                }

                if (!res.ok) {
                    alert(data.message || '创建会议失败');
                    return;
                }

                closeCreateModal();
                document.getElementById('new-title').value = '';
                document.getElementById('new-topic').value = '';
                document.getElementById('new-rounds').value = '5';
                await loadMeetings();
            } catch (e) {
                console.error('Failed to create meeting:', e);
                alert('网络错误，创建会议失败');
            }
        }

        // --- 会议控制台 ---
        async function openMeeting(id) {
            currentMeetingId = id;
            showPage('detail');
            setupSSE(id);
            refreshMeetingData();
        }

        async function refreshMeetingData() {
            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {
                headers: {'Authorization': `Bearer ${token}`}
            });
            const m = await res.json();

            document.getElementById('detail-title').textContent = m.title;
            document.getElementById('set-topic').value = m.topic;
            document.getElementById('set-rounds').value = m.max_rounds;
            document.getElementById('detail-invite-code').textContent = m.invite_code;
            document.querySelectorAll('.invite-placeholder').forEach(el => el.textContent = m.invite_code);

            // Agents
            const list = document.getElementById('agent-list');
            const select = document.getElementById('set-host');
            list.innerHTML = '';
            select.innerHTML = '<option value="">选择会议主持人</option>';

            m.agents.forEach(a => {
                const div = document.createElement('div');
                div.className = 'agent-item';
                div.innerHTML = `
                    <div class="agent-avatar">${getEmoji(a.role)}</div>
                    <div>
                        <div class="agent-name">${a.name}</div>
                        <div class="agent-role">${a.role}</div>
                    </div>
                `;
                list.appendChild(div);

                const opt = document.createElement('option');
                opt.value = a.name;
                opt.textContent = a.name;
                if (a.name === m.host_agent) opt.selected = true;
                select.appendChild(opt);
            });
            document.getElementById('agent-count').textContent = m.agents.length;

            updateControlUI(m.status);
        }

        function updateControlUI(status) {
            document.getElementById('btn-start-meeting').classList.add('hidden');
            document.getElementById('meeting-running-hint').classList.add('hidden');
            document.getElementById('meeting-finished-hint').classList.add('hidden');

            if (status === 'waiting') document.getElementById('btn-start-meeting').classList.remove('hidden');
            else if (status === 'running') document.getElementById('meeting-running-hint').classList.remove('hidden');
            else if (status === 'finished') document.getElementById('meeting-finished-hint').classList.remove('hidden');
        }

        async function saveSettings() {
            const topic = document.getElementById('set-topic').value;
            const max_rounds = document.getElementById('set-rounds').value;
            const host_agent = document.getElementById('set-host').value;

            await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                body: JSON.stringify({topic, max_rounds, host_agent})
            });
            alert('配置已同步');
        }

        async function startMeeting() {
            const host = document.getElementById('set-host').value;
            if (!host) return alert('请先指定一名龙虾作为会议主持人');

            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}/start`, {
                method: 'POST',
                headers: {'Authorization': `Bearer ${token}`}
            });
            const data = await res.json();
            if (data.success) updateControlUI('running');
            else alert(data.message);
        }

        function setupSSE(id) {
            if (sse) sse.close();
            document.getElementById('stream-flow').innerHTML = '';
            sse = new EventSource(`${API_BASE}/api/meetings/${id}/stream`);
            sse.onmessage = (e) => {
                const data = JSON.parse(e.data);
                handleStreamMsg(data);
            };
        }

        function handleStreamMsg(data) {
            const flow = document.getElementById('stream-flow');
            if (data.type === 'speech') {
                const div = document.createElement('div');
                div.className = 'msg-item';
                div.innerHTML = `
                    <div class="msg-header">
                        <span class="msg-author">🦞 ${data.agent}</span>
                        <span class="msg-tag">${data.role}</span>
                    </div>
                    <div class="msg-content">${data.content}</div>
                `;
                flow.appendChild(div);
                flow.scrollTop = flow.scrollHeight;
            } else if (data.type === 'round_start') {
                const div = document.createElement('div');
                div.className = 'msg-divider';
                div.innerHTML = `<span>第 ${data.round} 轮自由讨论</span>`;
                flow.appendChild(div);
            } else if (data.type === 'agent_registered') {
                refreshMeetingData();
            } else if (data.type === 'meeting_end') {
                updateControlUI('finished');
                const div = document.createElement('div');
                div.style = "text-align:center; padding:30px; color:var(--text-secondary); font-style: italic;";
                div.textContent = `———— 会议达成共识并结案：${data.reason} ————`;
                flow.appendChild(div);
            }
        }

        // --- Helpers ---
        function showPage(p) {
            document.querySelectorAll('.page').forEach(el => el.classList.remove('active'));
            document.getElementById(`page-${p}`).classList.add('active');
        }
        function goBack() { showPage('list'); loadMeetings(); if(sse) sse.close(); }
        function translateStatus(s) {
            return {waiting:'等待中', running:'进行中', finished:'已结束'}[s] || s;
        }
        function getEmoji(role) {
            const r = role.toLowerCase();
            if (r.includes('架构')) return '🏗️';
            if (r.includes('前端')) return '🎨';
            if (r.includes('后端')) return '⚙️';
            if (r.includes('产品')) return '📋';
            if (r.includes('测试')) return '🧪';
            return '🤖';
        }
        function toggleCode() { document.getElementById('join-code-box').classList.toggle('hidden'); }
        function copyInvite() {
            const code = document.getElementById('detail-invite-code').textContent;
            navigator.clipboard.writeText(code);
            alert('邀请码已复制到剪贴板');
        }

        // Init Check
        (async () => {
            if (token) {
                try {
                    const res = await fetch(`${API_BASE}/api/auth/me`, {headers: {'Authorization': `Bearer ${token}`}});
                    if (res.ok) {
                        currentUser = await res.json();
                        showPage('list');
                        loadMeetings();
                    } else logout();
                } catch(e) { logout(); }
            }
        })();
    </script>
</body>
</html>
'''

print(f"[startup] APP_HTML length={len(APP_HTML)}")

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
    if 'title' in data:
        m.title = data['title']
    if 'topic' in data:
        m.topic = data['topic']
    if 'max_rounds' in data:
        m.max_rounds = int(data['max_rounds'])
    if 'host_agent' in data:
        m.set_moderator(data['host_agent'])

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
    if not m:
        return jsonify({"message": "Not found"}), 404
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

        m = meetings[meeting_id]
        yield f"data: {json.dumps({'type': 'init', 'status': m.status, 'topic': m.topic})}\n\n"

        try:
            while True:
                msg = q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except GeneratorExit:
            if meeting_id in msg_queues:
                msg_queues[meeting_id].remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


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
    return Response(INDEX_HTML, mimetype='text/html')


@app.route('/app')
def app_page():
    return Response(APP_HTML, mimetype='text/html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7788))
    print(f"Starting V3 Meeting Server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
