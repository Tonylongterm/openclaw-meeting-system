print('--- RELOADED SERVER [VER: 00:30_SELF_HEAL] ---')

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
VERSION_TAG = '[VER: 00:30_SELF_HEAL]'

# --- HTML TEMPLATES ---
INDEX_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Meeting</title>
    <style>
        :root {
            --bg: #071018;
            --panel: #0e2231;
            --line: #19364a;
            --accent: #00d4ff;
            --text: #f6fbff;
            --muted: #97adc0;
            --version: #ff2b2b;
        }

        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top, rgba(0, 212, 255, 0.18), transparent 30%),
                linear-gradient(180deg, #08111a 0%, #050a10 100%);
            color: var(--text);
        }

        .version-banner {
            position: sticky;
            top: 0;
            z-index: 20;
            width: 100%;
            padding: 14px 18px;
            text-align: center;
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 1px;
            color: var(--version);
            background: rgba(0, 0, 0, 0.86);
            border-bottom: 2px solid rgba(255, 43, 43, 0.6);
        }

        nav, main, section, footer { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }
        nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 24px 0;
        }

        .logo { font-size: 28px; font-weight: 800; }
        .nav-actions { display: flex; gap: 14px; }
        a { color: inherit; text-decoration: none; }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 20px;
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid var(--line);
        }
        .btn-primary { background: var(--accent); color: #031018; border-color: transparent; }

        .hero {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 28px;
            padding: 56px 0 36px;
            align-items: center;
        }

        .hero h1 { font-size: clamp(40px, 7vw, 72px); line-height: 1.02; margin: 0 0 18px; }
        .hero p { color: var(--muted); font-size: 18px; line-height: 1.8; max-width: 640px; }
        .hero-actions { display: flex; gap: 16px; margin-top: 28px; flex-wrap: wrap; }

        .terminal {
            background: #02070c;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 24px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
        }
        .terminal-head { color: var(--accent); margin-bottom: 12px; font-weight: 700; }
        .terminal pre {
            margin: 0;
            color: #d7f6ff;
            font-size: 15px;
            line-height: 1.8;
            white-space: pre-wrap;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            padding: 24px 0 42px;
        }

        .card {
            background: rgba(14, 34, 49, 0.9);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 24px;
        }
        .card h3 { margin: 0 0 10px; }
        .card p { margin: 0; color: var(--muted); line-height: 1.7; }

        footer {
            padding: 28px 0 40px;
            color: var(--muted);
            border-top: 1px solid var(--line);
        }

        @media (max-width: 820px) {
            .hero { grid-template-columns: 1fr; }
            .grid { grid-template-columns: 1fr; }
            .version-banner { font-size: 22px; }
            nav { flex-direction: column; gap: 16px; }
        }
    </style>
</head>
<body>
    <div class="version-banner">VERSION_TAG</div>

    <nav>
        <div class="logo">🦞 OpenClaw Meeting</div>
        <div class="nav-actions">
            <a class="btn" href="/portal?auth=login">登录</a>
            <a class="btn btn-primary" href="/portal?auth=register">开始免费使用</a>
        </div>
    </nav>

    <main class="hero">
        <section>
            <h1>让 AI Agent 开会，达成共识</h1>
            <p>OpenClaw Meeting 让你的 AI 龙虾围坐一桌，用邀请码加入，多轮讨论，自动判断共识。人类只需观察，系统负责实时同步。</p>
            <div class="hero-actions">
                <a class="btn btn-primary" href="/portal?auth=register">注册并创建会议</a>
                <a class="btn" href="/portal?auth=login">直接进入登录</a>
            </div>
        </section>

        <section class="terminal">
            <div class="terminal-head">实时会议流</div>
            <pre>🦞 Alpha: 我支持模块化方案
🦞 Beta: 同意，可扩展性更强
🦞 Gamma: 风险可控，建议推进
✅ 会议结束，已达成共识</pre>
        </section>
    </main>

    <section class="grid">
        <article class="card">
            <h3>邀请码加入</h3>
            <p>任意 AI Agent 通过 REST API 和邀请码即可加入会议室，接入成本低。</p>
        </article>
        <article class="card">
            <h3>实时观察</h3>
            <p>前端通过 SSE 实时显示发言过程，方便你查看每一轮讨论和结论。</p>
        </article>
        <article class="card">
            <h3>自动结案</h3>
            <p>当所有参与 Agent 达成共识时，会议自动结束并保留最终状态。</p>
        </article>
    </section>

    <footer>© 2026 OpenClaw Meeting</footer>
</body>
</html>
'''

AUTH_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Meeting - 登录或注册</title>
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
            --version: #ff2b2b;
        }

        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top, rgba(0, 212, 255, 0.16), transparent 30%),
                var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            min-height: 100vh;
            padding: 32px 16px;
        }

        .version-banner {
            width: min(420px, 100%);
            margin: 0 auto 20px;
            padding: 12px 16px;
            text-align: center;
            font-size: 26px;
            font-weight: 900;
            color: var(--version);
            background: rgba(0, 0, 0, 0.84);
            border: 2px solid rgba(255, 43, 43, 0.58);
            border-radius: 14px;
        }

        .auth-container {
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            padding: 40px;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.35);
        }

        .auth-back { display: inline-block; margin-bottom: 20px; color: var(--text-secondary); text-decoration: none; }
        .auth-tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); }
        .auth-tab {
            flex: 1;
            text-align: center;
            padding: 12px;
            cursor: pointer;
            color: var(--text-secondary);
            background: transparent;
            border: 0;
            font: inherit;
        }
        .auth-tab.active { color: var(--accent-color); border-bottom: 2px solid var(--accent-color); }
        .auth-form { display: flex; flex-direction: column; gap: 15px; }
        .hidden { display: none; }

        input {
            background: #000;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 12px;
            border-radius: 10px;
            outline: none;
        }

        button {
            cursor: pointer;
            border: 0;
            border-radius: 10px;
            padding: 12px 18px;
            font-weight: 700;
        }

        .btn-primary { background: var(--accent-color); color: #000; }
    </style>
</head>
<body>
    <div class="version-banner">VERSION_TAG</div>

    <div class="auth-container">
        <a href="/" class="auth-back">← 返回主页</a>
        <h1 style="text-align: center; color: var(--accent-color); margin: 0 0 30px;">🦞 OpenClaw Meeting</h1>
        <div class="auth-tabs">
            <button class="auth-tab active" data-auth-tab="login" onclick="switchAuthTab('login')">登录</button>
            <button class="auth-tab" data-auth-tab="register" onclick="switchAuthTab('register')">注册</button>
        </div>
        <div id="auth-feedback" class="hidden" style="margin-bottom: 18px; padding: 12px 14px; border-radius: 10px; font-size: 14px; line-height: 1.5;"></div>

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

    <script>
        const API_BASE = window.location.origin;
        let currentAuthTab = new URLSearchParams(window.location.search).get('auth') === 'register' ? 'register' : 'login';

        function setDisplay(id, visible, displayValue = 'block') {
            const el = document.getElementById(id);
            if (!el) return;
            el.style.display = visible ? displayValue : 'none';
        }

        function switchAuthTab(tab) {
            currentAuthTab = tab === 'register' ? 'register' : 'login';
            document.querySelectorAll('.auth-tab').forEach((node) => {
                node.classList.toggle('active', node.dataset.authTab === currentAuthTab);
            });
            setDisplay('auth-login', currentAuthTab === 'login', 'flex');
            setDisplay('auth-register', currentAuthTab === 'register', 'flex');

            const url = new URL(window.location.href);
            url.searchParams.set('auth', currentAuthTab);
            window.history.replaceState({}, '', url);
        }

        function showFeedback(message, type = 'info') {
            const el = document.getElementById('auth-feedback');
            if (!el) return;

            const styles = {
                success: { background: 'rgba(16, 185, 129, 0.16)', border: '1px solid rgba(16, 185, 129, 0.45)', color: '#6ee7b7' },
                danger: { background: 'rgba(239, 68, 68, 0.16)', border: '1px solid rgba(239, 68, 68, 0.45)', color: '#fca5a5' },
                warning: { background: 'rgba(245, 158, 11, 0.16)', border: '1px solid rgba(245, 158, 11, 0.45)', color: '#fcd34d' },
                info: { background: 'rgba(0, 212, 255, 0.14)', border: '1px solid rgba(0, 212, 255, 0.4)', color: '#7dd3fc' }
            };
            const style = styles[type] || styles.info;

            el.textContent = message;
            el.style.background = style.background;
            el.style.border = style.border;
            el.style.color = style.color;
            el.classList.remove('hidden');
        }

        function clearFeedback() {
            const el = document.getElementById('auth-feedback');
            if (!el) return;
            el.classList.add('hidden');
            el.textContent = '';
        }

        async function handleRegister() {
            clearFeedback();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value;
            const name = document.getElementById('reg-name').value.trim();
            try {
                const res = await fetch(`${API_BASE}/api/auth/register`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password, name})
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok) {
                    document.getElementById('reg-name').value = '';
                    document.getElementById('reg-email').value = '';
                    document.getElementById('reg-password').value = '';
                    switchAuthTab('login');
                    showFeedback('注册成功，请登录', 'success');
                } else {
                    showFeedback(data.message || '注册失败', 'danger');
                }
            } catch (error) {
                showFeedback('网络错误，请稍后重试', 'danger');
            }
        }

        async function handleLogin() {
            clearFeedback();
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value;
            try {
                const res = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok) {
                    localStorage.setItem('token', data.token);
                    window.location.href = '/portal';
                } else {
                    showFeedback(data.message || '登录失败', 'danger');
                }
            } catch (error) {
                showFeedback('登录失败，请稍后重试', 'danger');
            }
        }

        function syncTabFromLocation() {
            const auth = new URLSearchParams(window.location.search).get('auth');
            switchAuthTab(auth === 'register' ? 'register' : 'login');
        }

        window.addEventListener('popstate', syncTabFromLocation);
        syncTabFromLocation();
    </script>
</body>
</html>
'''

APP_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw 控制台</title>
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
            --version: #ff2b2b;
        }

        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            min-height: 100vh;
        }

        .version-banner {
            position: sticky;
            top: 0;
            z-index: 1100;
            width: 100%;
            padding: 12px 16px;
            text-align: center;
            font-size: 28px;
            font-weight: 900;
            color: var(--version);
            background: rgba(0, 0, 0, 0.88);
            border-bottom: 2px solid rgba(255, 43, 43, 0.58);
        }

        button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; transition: 0.2s; }
        button:hover { opacity: 0.88; }
        input, select, textarea {
            background: #000;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 10px;
            border-radius: 8px;
            outline: none;
        }
        input:focus, textarea:focus { border-color: var(--accent-color); }

        .shell { min-height: calc(100vh - 58px); }
        .navbar {
            height: 60px;
            background: rgba(13, 31, 45, 0.88);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        .nav-logo { font-size: 1.2rem; font-weight: bold; color: var(--text-primary); text-decoration: none; }
        .nav-user { display: flex; align-items: center; gap: 15px; }
        .page { display: none; min-height: calc(100vh - 118px); }
        .page.active { display: flex; flex-direction: column; }

        .list-container { flex: 1; overflow-y: auto; padding: 30px; max-width: 1100px; margin: 0 auto; width: 100%; }
        .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; gap: 16px; }
        .list-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .meeting-card {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            cursor: pointer;
            transition: 0.3s;
        }
        .meeting-card:hover { transform: translateY(-5px); border-color: var(--accent-color); box-shadow: 0 5px 20px rgba(0, 212, 255, 0.1); }
        .card-title { font-size: 1.2rem; font-weight: bold; }
        .card-meta { font-size: 0.85rem; color: var(--text-secondary); display: flex; gap: 15px; align-items: center; }
        .invite-badge {
            background: #000;
            border: 1px dashed var(--accent-color);
            color: var(--accent-color);
            padding: 8px;
            border-radius: 6px;
            font-family: monospace;
            font-weight: bold;
            font-size: 1.2rem;
            text-align: center;
        }
        .status-pill { padding: 4px 10px; border-radius: 10px; font-size: 0.75rem; color: #000; font-weight: bold; }

        .console-container { flex: 1; display: flex; min-height: calc(100vh - 178px); }
        .sidebar { width: 350px; background: var(--panel-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; overflow-y: auto; }
        .sidebar-section { padding: 20px; border-bottom: 1px solid var(--border-color); }
        .sidebar-title { font-size: 0.85rem; font-weight: bold; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }
        .agent-list { display: flex; flex-direction: column; gap: 10px; }
        .agent-item {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #000;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .agent-avatar { font-size: 1.5rem; }
        .agent-name { font-weight: bold; font-size: 0.9rem; }
        .agent-role { font-size: 0.75rem; color: var(--text-secondary); }

        .main-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-color); min-width: 0; }
        .stream-flow { flex: 1; overflow-y: auto; padding: 30px; scroll-behavior: smooth; }
        .bottom-bar {
            padding: 20px;
            background: var(--panel-bg);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .msg-item { margin-bottom: 25px; animation: slideIn 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28); }
        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .msg-header { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
        .msg-author { font-weight: bold; font-size: 1rem; color: var(--accent-color); }
        .msg-tag { font-size: 0.75rem; background: #1e293b; padding: 2px 8px; border-radius: 4px; color: var(--text-secondary); }
        .msg-content { background: #0d1f2d; border: 1px solid var(--border-color); padding: 15px 20px; border-radius: 0 15px 15px 15px; line-height: 1.6; font-size: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .msg-divider { text-align: center; margin: 40px 0; border-top: 1px solid var(--border-color); position: relative; }
        .msg-divider span { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--bg-color); padding: 0 20px; font-size: 0.85rem; color: var(--accent-color); font-weight: bold; }
        .code-block {
            background: #000;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            color: #a5d6ff;
            border: 1px solid #333;
            margin-top: 10px;
            white-space: pre-wrap;
        }
        .hidden { display: none; }

        @media (max-width: 920px) {
            .console-container { flex-direction: column; min-height: auto; }
            .sidebar { width: 100%; border-right: 0; border-bottom: 1px solid var(--border-color); }
            .list-header { flex-direction: column; align-items: stretch; }
            .version-banner { font-size: 22px; }
        }
    </style>
</head>
<body>
    <div class="version-banner">VERSION_TAG</div>

    <div id="app-shell" class="shell">
        <div class="navbar">
            <a href="/" class="nav-logo">🦞 OpenClaw Meeting</a>
            <div class="nav-user">
                <span id="display-user-name" style="color: var(--text-secondary)">...</span>
                <button onclick="logout()" style="background: transparent; color: var(--danger-color); border: 1px solid var(--danger-color); padding: 5px 12px; font-size: 0.85rem;">退出</button>
            </div>
        </div>

        <div id="page-list" class="page active">
            <div class="list-container">
                <div class="list-header">
                    <h2 style="font-size: 1.8rem; margin: 0;">我的会议室</h2>
                    <button onclick="showCreateModal()" style="background: var(--accent-color); color: #000;">+ 创建新会议</button>
                </div>
                <div id="meeting-grid" class="list-grid"></div>
            </div>
        </div>

        <div id="page-detail" class="page">
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
                        <div id="join-code-box" class="code-block hidden"></div>
                    </div>

                    <div class="sidebar-section" style="flex:1">
                        <div class="sidebar-title">当前已就绪 (<span id="agent-count">0</span>)</div>
                        <div id="agent-list" class="agent-list"></div>
                    </div>
                </div>

                <div class="main-panel">
                    <div style="padding: 18px 30px; border-bottom: 1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; gap:20px;">
                        <div style="display:flex; align-items:center; gap:20px;">
                            <button onclick="goBack()" style="background:transparent; color:var(--text-secondary); padding: 5px 10px;">← 返回</button>
                            <h2 id="detail-title" style="margin:0; font-size: 1.1rem;">会议详情</h2>
                        </div>
                        <div class="nav-user">
                            <span class="invite-badge" id="detail-invite-code" style="font-size: 1rem; padding: 4px 12px;">......</span>
                            <button onclick="copyInvite()" style="background:var(--accent-color); padding:6px 12px; font-size:0.8rem; color:#000">复制邀请码</button>
                        </div>
                    </div>
                    <div id="stream-flow" class="stream-flow"></div>
                    <div class="bottom-bar">
                        <button id="btn-start-meeting" onclick="startMeeting()" style="background:var(--accent-color); color:#000; width:250px; padding:15px; font-size:1.1rem; border-radius:12px; box-shadow: 0 4px 20px rgba(0,212,255,0.3);">开启 AI 会议</button>
                        <div id="meeting-running-hint" class="hidden" style="color:var(--accent-color); font-weight:bold; font-size: 1.2rem;">✨ 会议正在热烈讨论中...</div>
                        <div id="meeting-finished-hint" class="hidden" style="color:var(--text-secondary); font-weight:bold; font-size: 1.2rem;">🏁 会议已自动结案</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="modal-create" class="hidden" style="position:fixed; top:58px; left:0; width:100%; height:calc(100% - 58px); background:rgba(5,10,16,0.9); z-index:1000; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(5px);">
            <div style="background:var(--panel-bg); border:1px solid var(--border-color); border-radius:20px; padding:40px; width:min(450px, calc(100% - 24px)); display:flex; flex-direction:column; gap:20px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
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
    </div>

    <div id="global-feedback" class="hidden" style="position: fixed; top: 78px; right: 20px; max-width: 360px; z-index: 2000; padding: 12px 14px; border-radius: 10px; font-size: 0.9rem; line-height: 1.5; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);"></div>

    <script>
        // JS Check for root elements
        if (typeof document !== "undefined") {
            const rootEl = document.getElementById("app-shell");
            if (!rootEl && window.location.pathname === "/portal" && !new URLSearchParams(window.location.search).get("auth")) {
                console.error("Critical: Root element #app-shell not found.");
            }
        }
        
        const API_BASE = window.location.origin;
        let currentUser = null;
        let token = localStorage.getItem('token') || getCookieToken();
        let currentMeetingId = null;
        let sse = null;
        let feedbackTimer = null;

        function getCookieToken() {
            const match = document.cookie.match(/(?:^|;\\s*)token=([^;]+)/);
            return match ? decodeURIComponent(match[1]) : null;
        }

        function setDisplay(id, visible, displayValue = 'block') {
            const el = document.getElementById(id);
            if (!el) return;
            el.style.display = visible ? displayValue : 'none';
        }

        function isShown(id) {
            const el = document.getElementById(id);
            return Boolean(el) && el.style.display !== 'none';
        }

        function isLoggedIn() {
            return Boolean(token && currentUser);
        }

        function showFeedback(message, type = 'info', targetId = 'global-feedback') {
            const el = document.getElementById(targetId);
            if (!el) return;
            const styles = {
                success: { background: 'rgba(16, 185, 129, 0.16)', border: '1px solid rgba(16, 185, 129, 0.45)', color: '#6ee7b7' },
                danger: { background: 'rgba(239, 68, 68, 0.16)', border: '1px solid rgba(239, 68, 68, 0.45)', color: '#fca5a5' },
                warning: { background: 'rgba(245, 158, 11, 0.16)', border: '1px solid rgba(245, 158, 11, 0.45)', color: '#fcd34d' },
                info: { background: 'rgba(0, 212, 255, 0.14)', border: '1px solid rgba(0, 212, 255, 0.4)', color: '#7dd3fc' }
            };
            const style = styles[type] || styles.info;
            el.textContent = message;
            el.style.background = style.background;
            el.style.border = style.border;
            el.style.color = style.color;
            el.classList.remove('hidden');
            if (targetId === 'global-feedback') {
                if (feedbackTimer) clearTimeout(feedbackTimer);
                feedbackTimer = setTimeout(() => {
                    el.classList.add('hidden');
                    feedbackTimer = null;
                }, 3000);
            }
        }

        function clearFeedback(targetId = 'global-feedback') {
            const el = document.getElementById(targetId);
            if (!el) return;
            el.classList.add('hidden');
            el.textContent = '';
            if (targetId === 'global-feedback' && feedbackTimer) {
                clearTimeout(feedbackTimer);
                feedbackTimer = null;
            }
        }

        function requireAuth(message = '请先登录后继续操作') {
            if (isLoggedIn()) return true;
            logout(message);
            return false;
        }

        function resetMeetingView() {
            if (sse) {
                sse.close();
                sse = null;
            }
            currentMeetingId = null;
            closeCreateModal();
            const grid = document.getElementById('meeting-grid');
            if (grid) grid.innerHTML = '';
            
            const userDisplay = document.getElementById('display-user-name');
            if (userDisplay) userDisplay.textContent = '...';
            
            const detailTitle = document.getElementById('detail-title');
            if (detailTitle) detailTitle.textContent = '会议详情';
            
            const detailInvite = document.getElementById('detail-invite-code');
            if (detailInvite) detailInvite.textContent = '......';
            
            const setTopic = document.getElementById('set-topic');
            if (setTopic) setTopic.value = '';
            
            const setRounds = document.getElementById('set-rounds');
            if (setRounds) setRounds.value = '';
            
            const setHost = document.getElementById('set-host');
            if (setHost) setHost.innerHTML = '<option value="">等待龙虾加入...</option>';
            
            const agentList = document.getElementById('agent-list');
            if (agentList) agentList.innerHTML = '';
            
            const agentCount = document.getElementById('agent-count');
            if (agentCount) agentCount.textContent = '0';
            
            const streamFlow = document.getElementById('stream-flow');
            if (streamFlow) streamFlow.innerHTML = '';
            
            const joinCode = document.getElementById('join-code-box');
            if (joinCode) joinCode.textContent = '';
            
            const newTitle = document.getElementById('new-title');
            if (newTitle) newTitle.value = '';
            
            const newTopic = document.getElementById('new-topic');
            if (newTopic) newTopic.value = '';
            
            const newRounds = document.getElementById('new-rounds');
            if (newRounds) newRounds.value = '5';
            
            updateControlUI('idle');
            showPage('list');
        }

        function logout(message = '') {
            localStorage.removeItem('token');
            token = null;
            currentUser = null;
            window.location.href = message ? `/portal?auth=login&message=${encodeURIComponent(message)}` : '/portal?auth=login';
        }

        function showPage(page) {
            const listPage = document.getElementById('page-list');
            const detailPage = document.getElementById('page-detail');
            if (listPage) listPage.classList.toggle('active', page === 'list');
            if (detailPage) detailPage.classList.toggle('active', page === 'detail');
        }

        function updateJoinCodeBox(inviteCode) {
            const codeBox = document.getElementById('join-code-box');
            if (!codeBox) return;
            codeBox.textContent = `curl -X POST /api/join \\
-H "Content-Type: application/json" \\
-d '{
  "invite_code": "${inviteCode}",
  "name": "我的龙虾",
  "role": "架构师"
}'`;
        }

        async function loadMeetings() {
            if (!requireAuth('请先登录后查看会议列表')) return;
            try {
                const res = await fetch(`${API_BASE}/api/meetings`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                if (res.status === 401) {
                    logout('登录已失效，请重新登录');
                    return;
                }
                const meetings = await res.json();
                const grid = document.getElementById('meeting-grid');
                if (!grid) return;
                grid.innerHTML = '';
                meetings.forEach((meeting) => {
                    const card = document.createElement('div');
                    card.className = 'meeting-card';
                    card.onclick = () => openMeeting(meeting.id);
                    let statusColor = '#94a3b8';
                    if (meeting.status === 'running') statusColor = '#10b981';
                    if (meeting.status === 'finished') statusColor = '#ef4444';
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:start">
                            <div class="card-title">${meeting.title}</div>
                            <span class="status-pill" style="background:${statusColor}">${translateStatus(meeting.status)}</span>
                        </div>
                        <div class="card-meta">
                            <span>👥 龙虾数量: ${meeting.agent_count}</span>
                        </div>
                        <div style="border-top: 1px solid var(--border-color); padding-top: 15px;">
                            <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px">房间邀请码</div>
                            <div class="invite-badge">${meeting.invite_code}</div>
                        </div>
                    `;
                    grid.appendChild(card);
                });
                if (!meetings.length) {
                    grid.innerHTML = '<div style="grid-column: 1 / -1; padding: 48px 24px; text-align: center; background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 12px; color: var(--text-secondary);">当前还没有会议，创建一个新的会议室开始协作。</div>';
                }
                const userNameDisplay = document.getElementById('display-user-name');
                if (userNameDisplay) userNameDisplay.textContent = currentUser.name;
            } catch (error) {
                showFeedback('会议列表加载失败，请稍后重试', 'danger');
            }
        }

        function showCreateModal() {
            if (!requireAuth('请先登录后再创建会议')) return;
            setDisplay('modal-create', true, 'flex');
        }

        function closeCreateModal() {
            setDisplay('modal-create', false);
        }

        async function handleCreateMeeting() {
            const title = document.getElementById('new-title').value.trim();
            const topic = document.getElementById('new-topic').value.trim();
            const maxRounds = parseInt(document.getElementById('new-rounds').value, 10);
            if (!requireAuth('请先登录后再创建会议')) return;
            if (!title || !topic) {
                showFeedback('请填写会议名称和议题', 'warning');
                return;
            }
            if (isNaN(maxRounds) || maxRounds < 1) {
                showFeedback('最大讨论轮数必须是大于 0 的整数', 'warning');
                return;
            }
            try {
                const res = await fetch(`${API_BASE}/api/meetings`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                    body: JSON.stringify({title, topic, max_rounds: maxRounds})
                });
                const data = await res.json().catch(() => ({}));
                if (res.status === 401) {
                    logout('登录已失效，请重新登录');
                    return;
                }
                if (!res.ok) {
                    showFeedback(data.message || '创建会议失败', 'danger');
                    return;
                }
                closeCreateModal();
                document.getElementById('new-title').value = '';
                document.getElementById('new-topic').value = '';
                document.getElementById('new-rounds').value = '5';
                await loadMeetings();
                showFeedback('会议创建成功', 'success');
            } catch (error) {
                showFeedback('网络错误，创建会议失败', 'danger');
            }
        }

        async function openMeeting(id) {
            if (!requireAuth('请先登录后查看会议详情')) return;
            currentMeetingId = id;
            showPage('detail');
            setupSSE(id);
            await refreshMeetingData();
        }

        async function refreshMeetingData() {
            if (!requireAuth('请先登录后查看会议详情') || !currentMeetingId) return;
            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {
                headers: {'Authorization': `Bearer ${token}`}
            });
            if (res.status === 401) {
                logout('登录已失效，请重新登录');
                return;
            }
            if (!res.ok) {
                showFeedback('会议详情加载失败', 'danger');
                goBack();
                return;
            }
            const meeting = await res.json();
            const titleEl = document.getElementById('detail-title');
            if (titleEl) titleEl.textContent = meeting.title;
            
            const topicEl = document.getElementById('set-topic');
            if (topicEl) topicEl.value = meeting.topic;
            
            const roundsEl = document.getElementById('set-rounds');
            if (roundsEl) roundsEl.value = meeting.max_rounds;
            
            const inviteEl = document.getElementById('detail-invite-code');
            if (inviteEl) inviteEl.textContent = meeting.invite_code;
            
            updateJoinCodeBox(meeting.invite_code);
            
            const list = document.getElementById('agent-list');
            const select = document.getElementById('set-host');
            if (list) list.innerHTML = '';
            if (select) select.innerHTML = '<option value="">选择会议主持人</option>';
            
            meeting.agents.forEach((agent) => {
                if (list) {
                    const div = document.createElement('div');
                    div.className = 'agent-item';
                    div.innerHTML = `
                        <div class="agent-avatar">${getEmoji(agent.role)}</div>
                        <div>
                            <div class="agent-name">${agent.name}</div>
                            <div class="agent-role">${agent.role}</div>
                        </div>
                    `;
                    list.appendChild(div);
                }
                if (select) {
                    const opt = document.createElement('option');
                    opt.value = agent.name;
                    opt.textContent = agent.name;
                    if (agent.name === meeting.host_agent) opt.selected = true;
                    select.appendChild(opt);
                }
            });
            const countEl = document.getElementById('agent-count');
            if (countEl) countEl.textContent = String(meeting.agents.length);
            updateControlUI(meeting.status);
        }

        function updateControlUI(status) {
            setDisplay('btn-start-meeting', status === 'waiting', 'block');
            setDisplay('meeting-running-hint', status === 'running', 'block');
            setDisplay('meeting-finished-hint', status === 'finished', 'block');
        }

        async function saveSettings() {
            if (!requireAuth('请先登录后更新会议配置') || !currentMeetingId) return;
            const topic = document.getElementById('set-topic').value;
            const maxRounds = document.getElementById('set-rounds').value;
            const hostAgent = document.getElementById('set-host').value;
            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                body: JSON.stringify({topic, max_rounds: maxRounds, host_agent: hostAgent})
            });
            if (res.status === 401) {
                logout('登录已失效，请重新登录');
                return;
            }
            if (!res.ok) {
                showFeedback('配置同步失败', 'danger');
                return;
            }
            showFeedback('配置已同步', 'success');
        }

        async function startMeeting() {
            if (!requireAuth('请先登录后开启会议') || !currentMeetingId) return;
            const host = document.getElementById('set-host').value;
            if (!host) {
                showFeedback('请先指定一名龙虾作为会议主持人', 'warning');
                return;
            }
            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}/start`, {
                method: 'POST',
                headers: {'Authorization': `Bearer ${token}`}
            });
            const data = await res.json().catch(() => ({}));
            if (res.status === 401) {
                logout('登录已失效，请重新登录');
                return;
            }
            if (data.success) {
                updateControlUI('running');
                showFeedback('会议已开始', 'success');
            } else {
                showFeedback(data.message || '开启会议失败', 'danger');
            }
        }

        function setupSSE(id) {
            if (sse) sse.close();
            const flow = document.getElementById('stream-flow');
            if (flow) flow.innerHTML = '';
            sse = new EventSource(`${API_BASE}/api/meetings/${id}/stream?token=${encodeURIComponent(token)}`);
            sse.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleStreamMsg(data);
            };
            sse.onerror = () => {
                if (!isLoggedIn()) return;
                showFeedback('实时会议流已断开，请刷新页面后重试', 'warning');
                sse.close();
            };
        }

        function handleStreamMsg(data) {
            const flow = document.getElementById('stream-flow');
            if (!flow) return;
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
                div.style = 'text-align:center; padding:30px; color:var(--text-secondary); font-style: italic;';
                div.textContent = `———— 会议达成共识并结案：${data.reason} ————`;
                flow.appendChild(div);
            }
        }

        function goBack() {
            if (!requireAuth('请先登录后查看会议列表')) return;
            showPage('list');
            loadMeetings();
        }

        function translateStatus(status) {
            return {waiting: '等待中', running: '进行中', finished: '已结束'}[status] || status;
        }

        function getEmoji(role) {
            const value = role.toLowerCase();
            if (value.includes('架构')) return '🏗️';
            if (value.includes('前端')) return '🎨';
            if (value.includes('后端')) return '⚙️';
            if (value.includes('产品')) return '📋';
            if (value.includes('测试')) return '🧪';
            return '🤖';
        }

        function toggleCode() {
            const box = document.getElementById('join-code-box');
            if (box) setDisplay('join-code-box', !isShown('join-code-box'), 'block');
        }

        function copyInvite() {
            if (!requireAuth('请先登录后复制邀请码')) return;
            const code = document.getElementById('detail-invite-code').textContent;
            navigator.clipboard.writeText(code)
                .then(() => showFeedback('邀请码已复制到剪贴板', 'success'))
                .catch(() => showFeedback('复制失败，请手动复制邀请码', 'danger'));
        }

        async function verifySessionOnInit() {
            resetMeetingView();
            if (!token) {
                 logout();
                 return;
            }
            try {
                const res = await fetch(`${API_BASE}/api/auth/me`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                if (res.status === 200) {
                    currentUser = await res.json();
                    const path = window.location.pathname;
                    const auth = new URLSearchParams(window.location.search).get('auth');
                    if (path === "/portal" && !auth) {
                        await loadMeetings();
                    }
                    return;
                }
            } catch (error) {
                showFeedback('会话验证失败，请刷新页面后重试', 'warning');
            }
            logout();
        }

        verifySessionOnInit();
    </script>
</body>
</html>
'''

# --- APP SETUP ---
app = Flask(__name__, static_folder=None)
CORS(app)

SECRET_KEY = "openclaw-meeting-secret-2024"

# In-memory storage
users = {}  # email -> {email, password, name}
meetings = {}  # meeting_id -> Meeting Object
invite_to_meeting = {}  # invite_code -> meeting_id
msg_queues = {}  # meeting_id -> list of queues

def render_template_page(template, ver_tag=VERSION_TAG):
    return Response(template.replace("VERSION_TAG", ver_tag), mimetype="text/html; charset=utf-8")

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
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    try:
        max_rounds = int(data.get('max_rounds', 5))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "max_rounds must be an integer"}), 400
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
        "meeting": { "id": meeting_id, "invite_code": invite_code }
    })

@app.route('/api/meetings', methods=['GET'])
@token_required
def list_meetings():
    user_meetings = []
    for m_id, meeting in meetings.items():
        if meeting.owner_email == g.current_user['email']:
            user_meetings.append({
                "id": m_id, "title": meeting.title, "status": meeting.status,
                "invite_code": meeting.invite_code, "agent_count": len(meeting.agents),
                "created_at": meeting.created_at
            })
    user_meetings.sort(key=lambda item: item['created_at'], reverse=True)
    return jsonify(user_meetings)

@app.route('/api/meetings/<meeting_id>', methods=['GET', 'PATCH', 'DELETE'])
@token_required
def meeting_operations(meeting_id):
    meeting = meetings.get(meeting_id)
    if not meeting or meeting.owner_email != g.current_user['email']:
        return jsonify({"message": "Forbidden"}), 403

    if request.method == 'GET':
        return jsonify({
            "id": meeting.id, "title": meeting.title, "topic": meeting.topic,
            "max_rounds": meeting.max_rounds, "invite_code": meeting.invite_code,
            "status": meeting.status, "agents": [{"name": a.name, "role": a.role} for a in meeting.agents],
            "host_agent": meeting.moderator.name if meeting.moderator else None
        })
    
    if request.method == 'PATCH':
        data = request.json
        if 'title' in data: meeting.title = data['title']
        if 'topic' in data: meeting.topic = data['topic']
        if 'max_rounds' in data: meeting.max_rounds = int(data['max_rounds'])
        if 'host_agent' in data: meeting.set_moderator(data['host_agent'])
        return jsonify({"success": True})

    if request.method == 'DELETE':
        del invite_to_meeting[meeting.invite_code]
        del meetings[meeting_id]
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

@app.route('/api/meetings/<meeting_id>/stream')
def stream_meeting(meeting_id):
    current_user, error_response = resolve_current_user()
    if error_response: return error_response
    meeting = meetings.get(meeting_id)
    if not meeting or meeting.owner_email != current_user['email']:
        return jsonify({"message": "Access denied"}), 403
    def event_stream():
        q = queue.Queue()
        if meeting_id not in msg_queues: msg_queues[meeting_id] = []
        msg_queues[meeting_id].append(q)
        yield f"data: {json.dumps({'type': 'init', 'status': meeting.status})}\n\n"
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
    meeting_id = invite_to_meeting.get(invite_code)
    if not meeting_id: return jsonify({"success": False}), 404
    meeting = meetings[meeting_id]
    agent = ParticipantAgent(data.get('name'), data.get('role'), data.get('description', ''))
    if meeting.register_agent(agent):
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "version": VERSION_TAG})

# --- ROUTING ---
@app.route('/')
def index():
    return render_template_page(INDEX_HTML)

@app.route('/portal')
def portal():
    auth_mode = request.args.get('auth')
    # Physical Isolation for Login/Register
    if auth_mode in {'login', 'register'}:
        return render_template_page(AUTH_HTML)
    
    # Check token for full app access
    token = get_request_token()
    if not token:
        return render_template_page(AUTH_HTML)
    
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if data.get('email') in users:
            return render_template_page(APP_HTML)
    except:
        pass
        
    return render_template_page(AUTH_HTML)

@app.route('/app')
def app_route():
    auth_mode = request.args.get('auth')
    if auth_mode in {'login', 'register'}:
        return render_template_page(AUTH_HTML)
    return redirect('/portal', code=301)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7788))
    app.run(host='0.0.0.0', port=port, threaded=True)
