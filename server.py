print('--- RELOADED SERVER V23:55 ULTIMATE STABLE (EMBEDDED HTML) ---')

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
VERSION_TAG = '[VER: 23:55_ULTIMATE_STABLE]'
EMBEDDED_HTML = {
    "index": '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset=\'UTF-8\'>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>OpenClaw Meeting</title>\n    <style>\n        :root {\n            --bg: #071018;\n            --panel: #0e2231;\n            --line: #19364a;\n            --accent: #00d4ff;\n            --text: #f6fbff;\n            --muted: #97adc0;\n            --version: #ff2b2b;\n        }\n\n        * { box-sizing: border-box; }\n        body {\n            margin: 0;\n            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;\n            background:\n                radial-gradient(circle at top, rgba(0, 212, 255, 0.18), transparent 30%),\n                linear-gradient(180deg, #08111a 0%, #050a10 100%);\n            color: var(--text);\n        }\n\n        .version-banner {\n            position: sticky;\n            top: 0;\n            z-index: 20;\n            width: 100%;\n            padding: 14px 18px;\n            text-align: center;\n            font-size: 28px;\n            font-weight: 900;\n            letter-spacing: 1px;\n            color: var(--version);\n            background: rgba(0, 0, 0, 0.86);\n            border-bottom: 2px solid rgba(255, 43, 43, 0.6);\n        }\n\n        nav, main, section, footer { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }\n        nav {\n            display: flex;\n            align-items: center;\n            justify-content: space-between;\n            padding: 24px 0;\n        }\n\n        .logo { font-size: 28px; font-weight: 800; }\n        .nav-actions { display: flex; gap: 14px; }\n        a { color: inherit; text-decoration: none; }\n        .btn {\n            display: inline-flex;\n            align-items: center;\n            justify-content: center;\n            padding: 12px 20px;\n            border-radius: 12px;\n            font-weight: 700;\n            border: 1px solid var(--line);\n        }\n        .btn-primary { background: var(--accent); color: #031018; border-color: transparent; }\n\n        .hero {\n            display: grid;\n            grid-template-columns: 1.2fr 1fr;\n            gap: 28px;\n            padding: 56px 0 36px;\n            align-items: center;\n        }\n\n        .hero h1 { font-size: clamp(40px, 7vw, 72px); line-height: 1.02; margin: 0 0 18px; }\n        .hero p { color: var(--muted); font-size: 18px; line-height: 1.8; max-width: 640px; }\n        .hero-actions { display: flex; gap: 16px; margin-top: 28px; flex-wrap: wrap; }\n\n        .terminal {\n            background: #02070c;\n            border: 1px solid var(--line);\n            border-radius: 22px;\n            padding: 24px;\n            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);\n        }\n        .terminal-head { color: var(--accent); margin-bottom: 12px; font-weight: 700; }\n        .terminal pre {\n            margin: 0;\n            color: #d7f6ff;\n            font-size: 15px;\n            line-height: 1.8;\n            white-space: pre-wrap;\n        }\n\n        .grid {\n            display: grid;\n            grid-template-columns: repeat(3, minmax(0, 1fr));\n            gap: 18px;\n            padding: 24px 0 42px;\n        }\n\n        .card {\n            background: rgba(14, 34, 49, 0.9);\n            border: 1px solid var(--line);\n            border-radius: 18px;\n            padding: 24px;\n        }\n        .card h3 { margin: 0 0 10px; }\n        .card p { margin: 0; color: var(--muted); line-height: 1.7; }\n\n        footer {\n            padding: 28px 0 40px;\n            color: var(--muted);\n            border-top: 1px solid var(--line);\n        }\n\n        @media (max-width: 820px) {\n            .hero { grid-template-columns: 1fr; }\n            .grid { grid-template-columns: 1fr; }\n            .version-banner { font-size: 22px; }\n            nav { flex-direction: column; gap: 16px; }\n        }\n    </style>\n</head>\n<body>\n    <div class="version-banner">[VER: 23:55_ULTIMATE_STABLE]</div>\n\n    <nav>\n        <div class="logo">\U0001f99e OpenClaw Meeting</div>\n        <div class="nav-actions">\n            <a class="btn" href="/app?auth=login">\u767b\u5f55</a>\n            <a class="btn btn-primary" href="/app?auth=register">\u5f00\u59cb\u514d\u8d39\u4f7f\u7528</a>\n        </div>\n    </nav>\n\n    <main class="hero">\n        <section>\n            <h1>\u8ba9 AI Agent \u5f00\u4f1a\uff0c\u8fbe\u6210\u5171\u8bc6</h1>\n            <p>OpenClaw Meeting \u8ba9\u4f60\u7684 AI \u9f99\u867e\u56f4\u5750\u4e00\u684c\uff0c\u7528\u9080\u8bf7\u7801\u52a0\u5165\uff0c\u591a\u8f6e\u8ba8\u8bba\uff0c\u81ea\u52a8\u5224\u65ad\u5171\u8bc6\u3002\u4eba\u7c7b\u53ea\u9700\u89c2\u5bdf\uff0c\u7cfb\u7edf\u8d1f\u8d23\u5b9e\u65f6\u540c\u6b65\u3002</p>\n            <div class="hero-actions">\n                <a class="btn btn-primary" href="/app?auth=register">\u6ce8\u518c\u5e76\u521b\u5efa\u4f1a\u8bae</a>\n                <a class="btn" href="/app?auth=login">\u76f4\u63a5\u8fdb\u5165\u767b\u5f55</a>\n            </div>\n        </section>\n\n        <section class="terminal">\n            <div class="terminal-head">\u5b9e\u65f6\u4f1a\u8bae\u6d41</div>\n            <pre>\U0001f99e Alpha: \u6211\u652f\u6301\u6a21\u5757\u5316\u65b9\u6848\n\U0001f99e Beta: \u540c\u610f\uff0c\u53ef\u6269\u5c55\u6027\u66f4\u5f3a\n\U0001f99e Gamma: \u98ce\u9669\u53ef\u63a7\uff0c\u5efa\u8bae\u63a8\u8fdb\n\u2705 \u4f1a\u8bae\u7ed3\u675f\uff0c\u5df2\u8fbe\u6210\u5171\u8bc6</pre>\n        </section>\n    </main>\n\n    <section class="grid">\n        <article class="card">\n            <h3>\u9080\u8bf7\u7801\u52a0\u5165</h3>\n            <p>\u4efb\u610f AI Agent \u901a\u8fc7 REST API \u548c\u9080\u8bf7\u7801\u5373\u53ef\u52a0\u5165\u4f1a\u8bae\u5ba4\uff0c\u63a5\u5165\u6210\u672c\u4f4e\u3002</p>\n        </article>\n        <article class="card">\n            <h3>\u5b9e\u65f6\u89c2\u5bdf</h3>\n            <p>\u524d\u7aef\u901a\u8fc7 SSE \u5b9e\u65f6\u663e\u793a\u53d1\u8a00\u8fc7\u7a0b\uff0c\u65b9\u4fbf\u4f60\u67e5\u770b\u6bcf\u4e00\u8f6e\u8ba8\u8bba\u548c\u7ed3\u8bba\u3002</p>\n        </article>\n        <article class="card">\n            <h3>\u81ea\u52a8\u7ed3\u6848</h3>\n            <p>\u5f53\u6240\u6709\u53c2\u4e0e Agent \u8fbe\u6210\u5171\u8bc6\u65f6\uff0c\u4f1a\u8bae\u81ea\u52a8\u7ed3\u675f\u5e76\u4fdd\u7559\u6700\u7ec8\u72b6\u6001\u3002</p>\n        </article>\n    </section>\n\n    <footer>\xa9 2026 OpenClaw Meeting</footer>\n</body>\n</html>\n',
    "auth": '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset=\'UTF-8\'>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>OpenClaw Meeting - \u767b\u5f55\u6216\u6ce8\u518c</title>\n    <style>\n        :root {\n            --bg-color: #050a10;\n            --panel-bg: #0d1f2d;\n            --border-color: #1e293b;\n            --text-primary: #ffffff;\n            --text-secondary: #94a3b8;\n            --accent-color: #00d4ff;\n            --success-color: #10b981;\n            --danger-color: #ef4444;\n            --warning-color: #f59e0b;\n            --version: #ff2b2b;\n        }\n\n        * { box-sizing: border-box; }\n        body {\n            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;\n            background:\n                radial-gradient(circle at top, rgba(0, 212, 255, 0.16), transparent 30%),\n                var(--bg-color);\n            color: var(--text-primary);\n            margin: 0;\n            min-height: 100vh;\n            padding: 32px 16px;\n        }\n\n        .version-banner {\n            width: min(420px, 100%);\n            margin: 0 auto 20px;\n            padding: 12px 16px;\n            text-align: center;\n            font-size: 26px;\n            font-weight: 900;\n            color: var(--version);\n            background: rgba(0, 0, 0, 0.84);\n            border: 2px solid rgba(255, 43, 43, 0.58);\n            border-radius: 14px;\n        }\n\n        .auth-container {\n            width: 100%;\n            max-width: 420px;\n            margin: 0 auto;\n            padding: 40px;\n            background: var(--panel-bg);\n            border: 1px solid var(--border-color);\n            border-radius: 16px;\n            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.35);\n        }\n\n        .auth-back { display: inline-block; margin-bottom: 20px; color: var(--text-secondary); text-decoration: none; }\n        .auth-tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); }\n        .auth-tab {\n            flex: 1;\n            text-align: center;\n            padding: 12px;\n            cursor: pointer;\n            color: var(--text-secondary);\n            background: transparent;\n            border: 0;\n            font: inherit;\n        }\n        .auth-tab.active { color: var(--accent-color); border-bottom: 2px solid var(--accent-color); }\n        .auth-form { display: flex; flex-direction: column; gap: 15px; }\n        .hidden { display: none; }\n\n        input {\n            background: #000;\n            border: 1px solid var(--border-color);\n            color: var(--text-primary);\n            padding: 12px;\n            border-radius: 10px;\n            outline: none;\n        }\n\n        button {\n            cursor: pointer;\n            border: 0;\n            border-radius: 10px;\n            padding: 12px 18px;\n            font-weight: 700;\n        }\n\n        .btn-primary { background: var(--accent-color); color: #000; }\n    </style>\n</head>\n<body>\n    <div class="version-banner">[VER: 23:55_ULTIMATE_STABLE]</div>\n\n    <div class="auth-container">\n        <a href="/" class="auth-back">\u2190 \u8fd4\u56de\u4e3b\u9875</a>\n        <h1 style="text-align: center; color: var(--accent-color); margin: 0 0 30px;">\U0001f99e OpenClaw Meeting</h1>\n        <div class="auth-tabs">\n            <button class="auth-tab active" data-auth-tab="login" onclick="switchAuthTab(\'login\')">\u767b\u5f55</button>\n            <button class="auth-tab" data-auth-tab="register" onclick="switchAuthTab(\'register\')">\u6ce8\u518c</button>\n        </div>\n        <div id="auth-feedback" class="hidden" style="margin-bottom: 18px; padding: 12px 14px; border-radius: 10px; font-size: 14px; line-height: 1.5;"></div>\n\n        <div id="auth-login" class="auth-form">\n            <input type="email" id="login-email" placeholder="\u90ae\u7bb1\u5730\u5740">\n            <input type="password" id="login-password" placeholder="\u5bc6\u7801">\n            <button class="btn-primary" onclick="handleLogin()">\u767b\u5f55\u63a7\u5236\u53f0</button>\n        </div>\n\n        <div id="auth-register" class="auth-form hidden">\n            <input type="text" id="reg-name" placeholder="\u60a8\u7684\u59d3\u540d">\n            <input type="email" id="reg-email" placeholder="\u7535\u5b50\u90ae\u7bb1">\n            <input type="password" id="reg-password" placeholder="\u8bbe\u7f6e\u5bc6\u7801">\n            <button class="btn-primary" onclick="handleRegister()" style="background: var(--success-color);">\u514d\u8d39\u6ce8\u518c</button>\n        </div>\n    </div>\n\n    <script>\n        const API_BASE = window.location.origin;\n        let currentAuthTab = new URLSearchParams(window.location.search).get(\'auth\') === \'register\' ? \'register\' : \'login\';\n\n        function setDisplay(id, visible, displayValue = \'block\') {\n            const el = document.getElementById(id);\n            if (!el) return;\n            el.style.display = visible ? displayValue : \'none\';\n        }\n\n        function switchAuthTab(tab) {\n            currentAuthTab = tab === \'register\' ? \'register\' : \'login\';\n            document.querySelectorAll(\'.auth-tab\').forEach((node) => {\n                node.classList.toggle(\'active\', node.dataset.authTab === currentAuthTab);\n            });\n            setDisplay(\'auth-login\', currentAuthTab === \'login\', \'flex\');\n            setDisplay(\'auth-register\', currentAuthTab === \'register\', \'flex\');\n\n            const url = new URL(window.location.href);\n            url.searchParams.set(\'auth\', currentAuthTab);\n            window.history.replaceState({}, \'\', url);\n        }\n\n        function showFeedback(message, type = \'info\') {\n            const el = document.getElementById(\'auth-feedback\');\n            if (!el) return;\n\n            const styles = {\n                success: { background: \'rgba(16, 185, 129, 0.16)\', border: \'1px solid rgba(16, 185, 129, 0.45)\', color: \'#6ee7b7\' },\n                danger: { background: \'rgba(239, 68, 68, 0.16)\', border: \'1px solid rgba(239, 68, 68, 0.45)\', color: \'#fca5a5\' },\n                warning: { background: \'rgba(245, 158, 11, 0.16)\', border: \'1px solid rgba(245, 158, 11, 0.45)\', color: \'#fcd34d\' },\n                info: { background: \'rgba(0, 212, 255, 0.14)\', border: \'1px solid rgba(0, 212, 255, 0.4)\', color: \'#7dd3fc\' }\n            };\n            const style = styles[type] || styles.info;\n\n            el.textContent = message;\n            el.style.background = style.background;\n            el.style.border = style.border;\n            el.style.color = style.color;\n            el.classList.remove(\'hidden\');\n        }\n\n        function clearFeedback() {\n            const el = document.getElementById(\'auth-feedback\');\n            if (!el) return;\n            el.classList.add(\'hidden\');\n            el.textContent = \'\';\n        }\n\n        async function handleRegister() {\n            clearFeedback();\n            const email = document.getElementById(\'reg-email\').value.trim();\n            const password = document.getElementById(\'reg-password\').value;\n            const name = document.getElementById(\'reg-name\').value.trim();\n            try {\n                const res = await fetch(`${API_BASE}/api/auth/register`, {\n                    method: \'POST\',\n                    headers: {\'Content-Type\': \'application/json\'},\n                    body: JSON.stringify({email, password, name})\n                });\n                const data = await res.json().catch(() => ({}));\n                if (res.ok) {\n                    document.getElementById(\'reg-name\').value = \'\';\n                    document.getElementById(\'reg-email\').value = \'\';\n                    document.getElementById(\'reg-password\').value = \'\';\n                    switchAuthTab(\'login\');\n                    showFeedback(\'\u6ce8\u518c\u6210\u529f\uff0c\u8bf7\u767b\u5f55\', \'success\');\n                } else {\n                    showFeedback(data.message || \'\u6ce8\u518c\u5931\u8d25\', \'danger\');\n                }\n            } catch (error) {\n                showFeedback(\'\u7f51\u7edc\u9519\u8bef\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\', \'danger\');\n            }\n        }\n\n        async function handleLogin() {\n            clearFeedback();\n            const email = document.getElementById(\'login-email\').value.trim();\n            const password = document.getElementById(\'login-password\').value;\n            try {\n                const res = await fetch(`${API_BASE}/api/auth/login`, {\n                    method: \'POST\',\n                    headers: {\'Content-Type\': \'application/json\'},\n                    body: JSON.stringify({email, password})\n                });\n                const data = await res.json().catch(() => ({}));\n                if (res.ok) {\n                    localStorage.setItem(\'token\', data.token);\n                    window.location.href = \'/app\';\n                } else {\n                    showFeedback(data.message || \'\u767b\u5f55\u5931\u8d25\', \'danger\');\n                }\n            } catch (error) {\n                showFeedback(\'\u767b\u5f55\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\', \'danger\');\n            }\n        }\n\n        function syncTabFromLocation() {\n            const auth = new URLSearchParams(window.location.search).get(\'auth\');\n            switchAuthTab(auth === \'register\' ? \'register\' : \'login\');\n        }\n\n        window.addEventListener(\'popstate\', syncTabFromLocation);\n        syncTabFromLocation();\n    </script>\n</body>\n</html>\n',
    "app": '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset=\'UTF-8\'>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>OpenClaw \u63a7\u5236\u53f0</title>\n    <style>\n        :root {\n            --bg-color: #050a10;\n            --panel-bg: #0d1f2d;\n            --border-color: #1e293b;\n            --text-primary: #ffffff;\n            --text-secondary: #94a3b8;\n            --accent-color: #00d4ff;\n            --success-color: #10b981;\n            --danger-color: #ef4444;\n            --warning-color: #f59e0b;\n            --version: #ff2b2b;\n        }\n\n        * { box-sizing: border-box; }\n        body {\n            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;\n            background-color: var(--bg-color);\n            color: var(--text-primary);\n            margin: 0;\n            min-height: 100vh;\n        }\n\n        .version-banner {\n            position: sticky;\n            top: 0;\n            z-index: 1100;\n            width: 100%;\n            padding: 12px 16px;\n            text-align: center;\n            font-size: 28px;\n            font-weight: 900;\n            color: var(--version);\n            background: rgba(0, 0, 0, 0.88);\n            border-bottom: 2px solid rgba(255, 43, 43, 0.58);\n        }\n\n        button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; transition: 0.2s; }\n        button:hover { opacity: 0.88; }\n        input, select, textarea {\n            background: #000;\n            border: 1px solid var(--border-color);\n            color: var(--text-primary);\n            padding: 10px;\n            border-radius: 8px;\n            outline: none;\n        }\n        input:focus, textarea:focus { border-color: var(--accent-color); }\n\n        .shell { min-height: calc(100vh - 58px); }\n        .navbar {\n            height: 60px;\n            background: rgba(13, 31, 45, 0.88);\n            backdrop-filter: blur(10px);\n            border-bottom: 1px solid var(--border-color);\n            display: flex;\n            justify-content: space-between;\n            align-items: center;\n            padding: 0 20px;\n        }\n        .nav-logo { font-size: 1.2rem; font-weight: bold; color: var(--text-primary); text-decoration: none; }\n        .nav-user { display: flex; align-items: center; gap: 15px; }\n        .page { display: none; min-height: calc(100vh - 118px); }\n        .page.active { display: flex; flex-direction: column; }\n\n        .list-container { flex: 1; overflow-y: auto; padding: 30px; max-width: 1100px; margin: 0 auto; width: 100%; }\n        .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; gap: 16px; }\n        .list-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }\n        .meeting-card {\n            background: var(--panel-bg);\n            border: 1px solid var(--border-color);\n            border-radius: 12px;\n            padding: 25px;\n            display: flex;\n            flex-direction: column;\n            gap: 15px;\n            cursor: pointer;\n            transition: 0.3s;\n        }\n        .meeting-card:hover { transform: translateY(-5px); border-color: var(--accent-color); box-shadow: 0 5px 20px rgba(0, 212, 255, 0.1); }\n        .card-title { font-size: 1.2rem; font-weight: bold; }\n        .card-meta { font-size: 0.85rem; color: var(--text-secondary); display: flex; gap: 15px; align-items: center; }\n        .invite-badge {\n            background: #000;\n            border: 1px dashed var(--accent-color);\n            color: var(--accent-color);\n            padding: 8px;\n            border-radius: 6px;\n            font-family: monospace;\n            font-weight: bold;\n            font-size: 1.2rem;\n            text-align: center;\n        }\n        .status-pill { padding: 4px 10px; border-radius: 10px; font-size: 0.75rem; color: #000; font-weight: bold; }\n\n        .console-container { flex: 1; display: flex; min-height: calc(100vh - 178px); }\n        .sidebar { width: 350px; background: var(--panel-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; overflow-y: auto; }\n        .sidebar-section { padding: 20px; border-bottom: 1px solid var(--border-color); }\n        .sidebar-title { font-size: 0.85rem; font-weight: bold; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }\n        .agent-list { display: flex; flex-direction: column; gap: 10px; }\n        .agent-item {\n            display: flex;\n            align-items: center;\n            gap: 10px;\n            background: #000;\n            padding: 12px;\n            border-radius: 8px;\n            border: 1px solid var(--border-color);\n        }\n        .agent-avatar { font-size: 1.5rem; }\n        .agent-name { font-weight: bold; font-size: 0.9rem; }\n        .agent-role { font-size: 0.75rem; color: var(--text-secondary); }\n\n        .main-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-color); min-width: 0; }\n        .stream-flow { flex: 1; overflow-y: auto; padding: 30px; scroll-behavior: smooth; }\n        .bottom-bar {\n            padding: 20px;\n            background: var(--panel-bg);\n            border-top: 1px solid var(--border-color);\n            display: flex;\n            justify-content: center;\n            align-items: center;\n        }\n        .msg-item { margin-bottom: 25px; animation: slideIn 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28); }\n        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }\n        .msg-header { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }\n        .msg-author { font-weight: bold; font-size: 1rem; color: var(--accent-color); }\n        .msg-tag { font-size: 0.75rem; background: #1e293b; padding: 2px 8px; border-radius: 4px; color: var(--text-secondary); }\n        .msg-content { background: #0d1f2d; border: 1px solid var(--border-color); padding: 15px 20px; border-radius: 0 15px 15px 15px; line-height: 1.6; font-size: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }\n        .msg-divider { text-align: center; margin: 40px 0; border-top: 1px solid var(--border-color); position: relative; }\n        .msg-divider span { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--bg-color); padding: 0 20px; font-size: 0.85rem; color: var(--accent-color); font-weight: bold; }\n        .code-block {\n            background: #000;\n            padding: 15px;\n            border-radius: 8px;\n            font-family: \'Fira Code\', monospace;\n            font-size: 0.85rem;\n            overflow-x: auto;\n            color: #a5d6ff;\n            border: 1px solid #333;\n            margin-top: 10px;\n            white-space: pre-wrap;\n        }\n        .hidden { display: none; }\n\n        @media (max-width: 920px) {\n            .console-container { flex-direction: column; min-height: auto; }\n            .sidebar { width: 100%; border-right: 0; border-bottom: 1px solid var(--border-color); }\n            .list-header { flex-direction: column; align-items: stretch; }\n            .version-banner { font-size: 22px; }\n        }\n    </style>\n</head>\n<body>\n    <div class="version-banner">[VER: 23:55_ULTIMATE_STABLE]</div>\n\n    <div id="app-shell" class="shell">\n        <div class="navbar">\n            <a href="/" class="nav-logo">\U0001f99e OpenClaw Meeting</a>\n            <div class="nav-user">\n                <span id="display-user-name" style="color: var(--text-secondary)">...</span>\n                <button onclick="logout()" style="background: transparent; color: var(--danger-color); border: 1px solid var(--danger-color); padding: 5px 12px; font-size: 0.85rem;">\u9000\u51fa</button>\n            </div>\n        </div>\n\n        <div id="page-list" class="page active">\n            <div class="list-container">\n                <div class="list-header">\n                    <h2 style="font-size: 1.8rem; margin: 0;">\u6211\u7684\u4f1a\u8bae\u5ba4</h2>\n                    <button onclick="showCreateModal()" style="background: var(--accent-color); color: #000;">+ \u521b\u5efa\u65b0\u4f1a\u8bae</button>\n                </div>\n                <div id="meeting-grid" class="list-grid"></div>\n            </div>\n        </div>\n\n        <div id="page-detail" class="page">\n            <div class="console-container">\n                <div class="sidebar">\n                    <div class="sidebar-section">\n                        <div class="sidebar-title">\u4f1a\u8bae\u6838\u5fc3\u914d\u7f6e</div>\n                        <div style="display:flex; flex-direction:column; gap:12px;">\n                            <div>\n                                <label style="font-size:0.75rem; color:var(--text-secondary); display:block; margin-bottom:5px;">\u8ba8\u8bba\u4e3b\u9898</label>\n                                <textarea id="set-topic" rows="4" style="width:100%"></textarea>\n                            </div>\n                            <div style="display:flex; align-items:center; justify-content:space-between">\n                                <label style="font-size:0.75rem; color:var(--text-secondary)">\u6700\u5927\u8ba8\u8bba\u8f6e\u6570</label>\n                                <input type="number" id="set-rounds" style="width:60px">\n                            </div>\n                            <div>\n                                <label style="font-size:0.75rem; color:var(--text-secondary); display:block; margin-bottom:5px;">\u4f1a\u8bae\u4e3b\u6301\u4eba</label>\n                                <select id="set-host" style="width:100%">\n                                    <option value="">\u7b49\u5f85\u9f99\u867e\u52a0\u5165...</option>\n                                </select>\n                            </div>\n                            <button onclick="saveSettings()" style="background:#1e293b; color:var(--accent-color); border: 1px solid var(--accent-color); margin-top:10px">\u66f4\u65b0\u914d\u7f6e</button>\n                        </div>\n                    </div>\n\n                    <div class="sidebar-section">\n                        <div class="sidebar-title" style="display:flex; justify-content:space-between">\n                            <span>\u9f99\u867e\u63a5\u5165 (REST API)</span>\n                            <a href="javascript:void(0)" onclick="toggleCode()" style="font-size:0.7rem; color:var(--accent-color); text-decoration:none">\u67e5\u770b\u8be6\u60c5</a>\n                        </div>\n                        <div id="join-code-box" class="code-block hidden"></div>\n                    </div>\n\n                    <div class="sidebar-section" style="flex:1">\n                        <div class="sidebar-title">\u5f53\u524d\u5df2\u5c31\u7eea (<span id="agent-count">0</span>)</div>\n                        <div id="agent-list" class="agent-list"></div>\n                    </div>\n                </div>\n\n                <div class="main-panel">\n                    <div style="padding: 18px 30px; border-bottom: 1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; gap:20px;">\n                        <div style="display:flex; align-items:center; gap:20px;">\n                            <button onclick="goBack()" style="background:transparent; color:var(--text-secondary); padding: 5px 10px;">\u2190 \u8fd4\u56de</button>\n                            <h2 id="detail-title" style="margin:0; font-size: 1.1rem;">\u4f1a\u8bae\u8be6\u60c5</h2>\n                        </div>\n                        <div class="nav-user">\n                            <span class="invite-badge" id="detail-invite-code" style="font-size: 1rem; padding: 4px 12px;">......</span>\n                            <button onclick="copyInvite()" style="background:var(--accent-color); padding:6px 12px; font-size:0.8rem; color:#000">\u590d\u5236\u9080\u8bf7\u7801</button>\n                        </div>\n                    </div>\n                    <div id="stream-flow" class="stream-flow"></div>\n                    <div class="bottom-bar">\n                        <button id="btn-start-meeting" onclick="startMeeting()" style="background:var(--accent-color); color:#000; width:250px; padding:15px; font-size:1.1rem; border-radius:12px; box-shadow: 0 4px 20px rgba(0,212,255,0.3);">\u5f00\u542f AI \u4f1a\u8bae</button>\n                        <div id="meeting-running-hint" class="hidden" style="color:var(--accent-color); font-weight:bold; font-size: 1.2rem;">\u2728 \u4f1a\u8bae\u6b63\u5728\u70ed\u70c8\u8ba8\u8bba\u4e2d...</div>\n                        <div id="meeting-finished-hint" class="hidden" style="color:var(--text-secondary); font-weight:bold; font-size: 1.2rem;">\U0001f3c1 \u4f1a\u8bae\u5df2\u81ea\u52a8\u7ed3\u6848</div>\n                    </div>\n                </div>\n            </div>\n        </div>\n\n        <div id="modal-create" class="hidden" style="position:fixed; top:58px; left:0; width:100%; height:calc(100% - 58px); background:rgba(5,10,16,0.9); z-index:1000; display:flex; align-items:center; justify-content:center; backdrop-filter: blur(5px);">\n            <div style="background:var(--panel-bg); border:1px solid var(--border-color); border-radius:20px; padding:40px; width:min(450px, calc(100% - 24px)); display:flex; flex-direction:column; gap:20px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">\n                <h3 style="font-size: 1.5rem; margin: 0;">\u521b\u5efa\u65b0\u4f1a\u8bae</h3>\n                <div>\n                    <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">\u4f1a\u8bae\u540d\u79f0</label>\n                    <input type="text" id="new-title" placeholder="\u4f8b\u5982\uff1aQ2 \u6280\u672f\u67b6\u6784\u9009\u578b" style="width:100%">\n                </div>\n                <div>\n                    <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">\u8ba8\u8bba\u8bae\u9898</label>\n                    <textarea id="new-topic" placeholder="\u8bf7\u8be6\u7ec6\u63cf\u8ff0\u9700\u8981 AI Agent \u4eec\u8ba8\u8bba\u5e76\u8fbe\u6210\u5171\u8bc6\u7684\u4e3b\u9898..." rows="4" style="width:100%"></textarea>\n                </div>\n                <div>\n                    <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:8px;">\u6700\u5927\u8ba8\u8bba\u8f6e\u6570</label>\n                    <input type="number" id="new-rounds" value="5" style="width:100%">\n                </div>\n                <div style="display:flex; gap:15px; justify-content:flex-end; margin-top: 10px;">\n                    <button onclick="closeCreateModal()" style="background:transparent; color:var(--text-secondary)">\u53d6\u6d88</button>\n                    <button onclick="handleCreateMeeting()" style="background:var(--accent-color); color:#000">\u786e\u8ba4\u521b\u5efa</button>\n                </div>\n            </div>\n        </div>\n    </div>\n\n    <div id="global-feedback" class="hidden" style="position: fixed; top: 78px; right: 20px; max-width: 360px; z-index: 2000; padding: 12px 14px; border-radius: 10px; font-size: 0.9rem; line-height: 1.5; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);"></div>\n\n    <script>\n        const API_BASE = window.location.origin;\n        let currentUser = null;\n        let token = localStorage.getItem(\'token\') || getCookieToken();\n        let currentMeetingId = null;\n        let sse = null;\n        let feedbackTimer = null;\n\n        function getCookieToken() {\n            const match = document.cookie.match(/(?:^|;\\\\s*)token=([^;]+)/);\n            return match ? decodeURIComponent(match[1]) : null;\n        }\n\n        function setDisplay(id, visible, displayValue = \'block\') {\n            const el = document.getElementById(id);\n            if (!el) return;\n            el.style.display = visible ? displayValue : \'none\';\n        }\n\n        function isShown(id) {\n            const el = document.getElementById(id);\n            return Boolean(el) && el.style.display !== \'none\';\n        }\n\n        function isLoggedIn() {\n            return Boolean(token && currentUser);\n        }\n\n        function showFeedback(message, type = \'info\', targetId = \'global-feedback\') {\n            const el = document.getElementById(targetId);\n            if (!el) return;\n            const styles = {\n                success: { background: \'rgba(16, 185, 129, 0.16)\', border: \'1px solid rgba(16, 185, 129, 0.45)\', color: \'#6ee7b7\' },\n                danger: { background: \'rgba(239, 68, 68, 0.16)\', border: \'1px solid rgba(239, 68, 68, 0.45)\', color: \'#fca5a5\' },\n                warning: { background: \'rgba(245, 158, 11, 0.16)\', border: \'1px solid rgba(245, 158, 11, 0.45)\', color: \'#fcd34d\' },\n                info: { background: \'rgba(0, 212, 255, 0.14)\', border: \'1px solid rgba(0, 212, 255, 0.4)\', color: \'#7dd3fc\' }\n            };\n            const style = styles[type] || styles.info;\n            el.textContent = message;\n            el.style.background = style.background;\n            el.style.border = style.border;\n            el.style.color = style.color;\n            el.classList.remove(\'hidden\');\n            if (targetId === \'global-feedback\') {\n                if (feedbackTimer) clearTimeout(feedbackTimer);\n                feedbackTimer = setTimeout(() => {\n                    el.classList.add(\'hidden\');\n                    feedbackTimer = null;\n                }, 3000);\n            }\n        }\n\n        function clearFeedback(targetId = \'global-feedback\') {\n            const el = document.getElementById(targetId);\n            if (!el) return;\n            el.classList.add(\'hidden\');\n            el.textContent = \'\';\n            if (targetId === \'global-feedback\' && feedbackTimer) {\n                clearTimeout(feedbackTimer);\n                feedbackTimer = null;\n            }\n        }\n\n        function requireAuth(message = \'\u8bf7\u5148\u767b\u5f55\u540e\u7ee7\u7eed\u64cd\u4f5c\') {\n            if (isLoggedIn()) return true;\n            logout(message);\n            return false;\n        }\n\n        function resetMeetingView() {\n            if (sse) {\n                sse.close();\n                sse = null;\n            }\n            currentMeetingId = null;\n            closeCreateModal();\n            document.getElementById(\'meeting-grid\').innerHTML = \'\';\n            document.getElementById(\'display-user-name\').textContent = \'...\';\n            document.getElementById(\'detail-title\').textContent = \'\u4f1a\u8bae\u8be6\u60c5\';\n            document.getElementById(\'detail-invite-code\').textContent = \'......\';\n            document.getElementById(\'set-topic\').value = \'\';\n            document.getElementById(\'set-rounds\').value = \'\';\n            document.getElementById(\'set-host\').innerHTML = \'<option value="">\u7b49\u5f85\u9f99\u867e\u52a0\u5165...</option>\';\n            document.getElementById(\'agent-list\').innerHTML = \'\';\n            document.getElementById(\'agent-count\').textContent = \'0\';\n            document.getElementById(\'stream-flow\').innerHTML = \'\';\n            document.getElementById(\'join-code-box\').textContent = \'\';\n            document.getElementById(\'new-title\').value = \'\';\n            document.getElementById(\'new-topic\').value = \'\';\n            document.getElementById(\'new-rounds\').value = \'5\';\n            updateControlUI(\'idle\');\n            showPage(\'list\');\n        }\n\n        function logout(message = \'\') {\n            localStorage.removeItem(\'token\');\n            token = null;\n            currentUser = null;\n            window.location.href = message ? `/app?auth=login&message=${encodeURIComponent(message)}` : \'/app?auth=login\';\n        }\n\n        function showPage(page) {\n            document.getElementById(\'page-list\').classList.toggle(\'active\', page === \'list\');\n            document.getElementById(\'page-detail\').classList.toggle(\'active\', page === \'detail\');\n        }\n\n        function updateJoinCodeBox(inviteCode) {\n            const codeBox = document.getElementById(\'join-code-box\');\n            codeBox.textContent = `curl -X POST /api/join \\\\\n-H "Content-Type: application/json" \\\\\n-d \'{\n  "invite_code": "${inviteCode}",\n  "name": "\u6211\u7684\u9f99\u867e",\n  "role": "\u67b6\u6784\u5e08"\n}\'`;\n        }\n\n        async function loadMeetings() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u67e5\u770b\u4f1a\u8bae\u5217\u8868\')) return;\n            try {\n                const res = await fetch(`${API_BASE}/api/meetings`, {\n                    headers: {\'Authorization\': `Bearer ${token}`}\n                });\n                if (res.status === 401) {\n                    logout(\'\u767b\u5f55\u5df2\u5931\u6548\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\');\n                    return;\n                }\n                const meetings = await res.json();\n                const grid = document.getElementById(\'meeting-grid\');\n                grid.innerHTML = \'\';\n                meetings.forEach((meeting) => {\n                    const card = document.createElement(\'div\');\n                    card.className = \'meeting-card\';\n                    card.onclick = () => openMeeting(meeting.id);\n                    let statusColor = \'#94a3b8\';\n                    if (meeting.status === \'running\') statusColor = \'#10b981\';\n                    if (meeting.status === \'finished\') statusColor = \'#ef4444\';\n                    card.innerHTML = `\n                        <div style="display:flex; justify-content:space-between; align-items:start">\n                            <div class="card-title">${meeting.title}</div>\n                            <span class="status-pill" style="background:${statusColor}">${translateStatus(meeting.status)}</span>\n                        </div>\n                        <div class="card-meta">\n                            <span>\U0001f465 \u9f99\u867e\u6570\u91cf: ${meeting.agent_count}</span>\n                        </div>\n                        <div style="border-top: 1px solid var(--border-color); padding-top: 15px;">\n                            <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px">\u623f\u95f4\u9080\u8bf7\u7801</div>\n                            <div class="invite-badge">${meeting.invite_code}</div>\n                        </div>\n                    `;\n                    grid.appendChild(card);\n                });\n                if (!meetings.length) {\n                    grid.innerHTML = \'<div style="grid-column: 1 / -1; padding: 48px 24px; text-align: center; background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 12px; color: var(--text-secondary);">\u5f53\u524d\u8fd8\u6ca1\u6709\u4f1a\u8bae\uff0c\u521b\u5efa\u4e00\u4e2a\u65b0\u7684\u4f1a\u8bae\u5ba4\u5f00\u59cb\u534f\u4f5c\u3002</div>\';\n                }\n                document.getElementById(\'display-user-name\').textContent = currentUser.name;\n            } catch (error) {\n                showFeedback(\'\u4f1a\u8bae\u5217\u8868\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\', \'danger\');\n            }\n        }\n\n        function showCreateModal() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u518d\u521b\u5efa\u4f1a\u8bae\')) return;\n            setDisplay(\'modal-create\', true, \'flex\');\n        }\n\n        function closeCreateModal() {\n            setDisplay(\'modal-create\', false);\n        }\n\n        async function handleCreateMeeting() {\n            const title = document.getElementById(\'new-title\').value.trim();\n            const topic = document.getElementById(\'new-topic\').value.trim();\n            const maxRounds = Number.parseInt(document.getElementById(\'new-rounds\').value, 10);\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u518d\u521b\u5efa\u4f1a\u8bae\')) return;\n            if (!title || !topic) {\n                showFeedback(\'\u8bf7\u586b\u5199\u4f1a\u8bae\u540d\u79f0\u548c\u8bae\u9898\', \'warning\');\n                return;\n            }\n            if (!Number.isInteger(maxRounds) || maxRounds < 1) {\n                showFeedback(\'\u6700\u5927\u8ba8\u8bba\u8f6e\u6570\u5fc5\u987b\u662f\u5927\u4e8e 0 \u7684\u6574\u6570\', \'warning\');\n                return;\n            }\n            try {\n                const res = await fetch(`${API_BASE}/api/meetings`, {\n                    method: \'POST\',\n                    headers: {\'Content-Type\': \'application/json\', \'Authorization\': `Bearer ${token}`},\n                    body: JSON.stringify({title, topic, max_rounds: maxRounds})\n                });\n                const data = await res.json().catch(() => ({}));\n                if (res.status === 401) {\n                    logout(\'\u767b\u5f55\u5df2\u5931\u6548\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\');\n                    return;\n                }\n                if (!res.ok) {\n                    showFeedback(data.message || \'\u521b\u5efa\u4f1a\u8bae\u5931\u8d25\', \'danger\');\n                    return;\n                }\n                closeCreateModal();\n                document.getElementById(\'new-title\').value = \'\';\n                document.getElementById(\'new-topic\').value = \'\';\n                document.getElementById(\'new-rounds\').value = \'5\';\n                await loadMeetings();\n                showFeedback(\'\u4f1a\u8bae\u521b\u5efa\u6210\u529f\', \'success\');\n            } catch (error) {\n                showFeedback(\'\u7f51\u7edc\u9519\u8bef\uff0c\u521b\u5efa\u4f1a\u8bae\u5931\u8d25\', \'danger\');\n            }\n        }\n\n        async function openMeeting(id) {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u67e5\u770b\u4f1a\u8bae\u8be6\u60c5\')) return;\n            currentMeetingId = id;\n            showPage(\'detail\');\n            setupSSE(id);\n            await refreshMeetingData();\n        }\n\n        async function refreshMeetingData() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u67e5\u770b\u4f1a\u8bae\u8be6\u60c5\') || !currentMeetingId) return;\n            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {\n                headers: {\'Authorization\': `Bearer ${token}`}\n            });\n            if (res.status === 401) {\n                logout(\'\u767b\u5f55\u5df2\u5931\u6548\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\');\n                return;\n            }\n            if (!res.ok) {\n                showFeedback(\'\u4f1a\u8bae\u8be6\u60c5\u52a0\u8f7d\u5931\u8d25\', \'danger\');\n                goBack();\n                return;\n            }\n            const meeting = await res.json();\n            document.getElementById(\'detail-title\').textContent = meeting.title;\n            document.getElementById(\'set-topic\').value = meeting.topic;\n            document.getElementById(\'set-rounds\').value = meeting.max_rounds;\n            document.getElementById(\'detail-invite-code\').textContent = meeting.invite_code;\n            updateJoinCodeBox(meeting.invite_code);\n            const list = document.getElementById(\'agent-list\');\n            const select = document.getElementById(\'set-host\');\n            list.innerHTML = \'\';\n            select.innerHTML = \'<option value="">\u9009\u62e9\u4f1a\u8bae\u4e3b\u6301\u4eba</option>\';\n            meeting.agents.forEach((agent) => {\n                const div = document.createElement(\'div\');\n                div.className = \'agent-item\';\n                div.innerHTML = `\n                    <div class="agent-avatar">${getEmoji(agent.role)}</div>\n                    <div>\n                        <div class="agent-name">${agent.name}</div>\n                        <div class="agent-role">${agent.role}</div>\n                    </div>\n                `;\n                list.appendChild(div);\n                const opt = document.createElement(\'option\');\n                opt.value = agent.name;\n                opt.textContent = agent.name;\n                if (agent.name === meeting.host_agent) opt.selected = true;\n                select.appendChild(opt);\n            });\n            document.getElementById(\'agent-count\').textContent = String(meeting.agents.length);\n            updateControlUI(meeting.status);\n        }\n\n        function updateControlUI(status) {\n            setDisplay(\'btn-start-meeting\', status === \'waiting\', \'block\');\n            setDisplay(\'meeting-running-hint\', status === \'running\', \'block\');\n            setDisplay(\'meeting-finished-hint\', status === \'finished\', \'block\');\n        }\n\n        async function saveSettings() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u66f4\u65b0\u4f1a\u8bae\u914d\u7f6e\') || !currentMeetingId) return;\n            const topic = document.getElementById(\'set-topic\').value;\n            const maxRounds = document.getElementById(\'set-rounds\').value;\n            const hostAgent = document.getElementById(\'set-host\').value;\n            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}`, {\n                method: \'PATCH\',\n                headers: {\'Content-Type\': \'application/json\', \'Authorization\': `Bearer ${token}`},\n                body: JSON.stringify({topic, max_rounds: maxRounds, host_agent: hostAgent})\n            });\n            if (res.status === 401) {\n                logout(\'\u767b\u5f55\u5df2\u5931\u6548\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\');\n                return;\n            }\n            if (!res.ok) {\n                showFeedback(\'\u914d\u7f6e\u540c\u6b65\u5931\u8d25\', \'danger\');\n                return;\n            }\n            showFeedback(\'\u914d\u7f6e\u5df2\u540c\u6b65\', \'success\');\n        }\n\n        async function startMeeting() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u5f00\u542f\u4f1a\u8bae\') || !currentMeetingId) return;\n            const host = document.getElementById(\'set-host\').value;\n            if (!host) {\n                showFeedback(\'\u8bf7\u5148\u6307\u5b9a\u4e00\u540d\u9f99\u867e\u4f5c\u4e3a\u4f1a\u8bae\u4e3b\u6301\u4eba\', \'warning\');\n                return;\n            }\n            const res = await fetch(`${API_BASE}/api/meetings/${currentMeetingId}/start`, {\n                method: \'POST\',\n                headers: {\'Authorization\': `Bearer ${token}`}\n            });\n            const data = await res.json().catch(() => ({}));\n            if (res.status === 401) {\n                logout(\'\u767b\u5f55\u5df2\u5931\u6548\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\');\n                return;\n            }\n            if (data.success) {\n                updateControlUI(\'running\');\n                showFeedback(\'\u4f1a\u8bae\u5df2\u5f00\u59cb\', \'success\');\n            } else {\n                showFeedback(data.message || \'\u5f00\u542f\u4f1a\u8bae\u5931\u8d25\', \'danger\');\n            }\n        }\n\n        function setupSSE(id) {\n            if (sse) sse.close();\n            document.getElementById(\'stream-flow\').innerHTML = \'\';\n            sse = new EventSource(`${API_BASE}/api/meetings/${id}/stream?token=${encodeURIComponent(token)}`);\n            sse.onmessage = (event) => {\n                const data = JSON.parse(event.data);\n                handleStreamMsg(data);\n            };\n            sse.onerror = () => {\n                if (!isLoggedIn()) return;\n                showFeedback(\'\u5b9e\u65f6\u4f1a\u8bae\u6d41\u5df2\u65ad\u5f00\uff0c\u8bf7\u5237\u65b0\u9875\u9762\u540e\u91cd\u8bd5\', \'warning\');\n                sse.close();\n            };\n        }\n\n        function handleStreamMsg(data) {\n            const flow = document.getElementById(\'stream-flow\');\n            if (data.type === \'speech\') {\n                const div = document.createElement(\'div\');\n                div.className = \'msg-item\';\n                div.innerHTML = `\n                    <div class="msg-header">\n                        <span class="msg-author">\U0001f99e ${data.agent}</span>\n                        <span class="msg-tag">${data.role}</span>\n                    </div>\n                    <div class="msg-content">${data.content}</div>\n                `;\n                flow.appendChild(div);\n                flow.scrollTop = flow.scrollHeight;\n            } else if (data.type === \'round_start\') {\n                const div = document.createElement(\'div\');\n                div.className = \'msg-divider\';\n                div.innerHTML = `<span>\u7b2c ${data.round} \u8f6e\u81ea\u7531\u8ba8\u8bba</span>`;\n                flow.appendChild(div);\n            } else if (data.type === \'agent_registered\') {\n                refreshMeetingData();\n            } else if (data.type === \'meeting_end\') {\n                updateControlUI(\'finished\');\n                const div = document.createElement(\'div\');\n                div.style = \'text-align:center; padding:30px; color:var(--text-secondary); font-style: italic;\';\n                div.textContent = `\u2014\u2014\u2014\u2014 \u4f1a\u8bae\u8fbe\u6210\u5171\u8bc6\u5e76\u7ed3\u6848\uff1a${data.reason} \u2014\u2014\u2014\u2014`;\n                flow.appendChild(div);\n            }\n        }\n\n        function goBack() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u67e5\u770b\u4f1a\u8bae\u5217\u8868\')) return;\n            showPage(\'list\');\n            loadMeetings();\n        }\n\n        function translateStatus(status) {\n            return {waiting: \'\u7b49\u5f85\u4e2d\', running: \'\u8fdb\u884c\u4e2d\', finished: \'\u5df2\u7ed3\u675f\'}[status] || status;\n        }\n\n        function getEmoji(role) {\n            const value = role.toLowerCase();\n            if (value.includes(\'\u67b6\u6784\')) return \'\U0001f3d7\ufe0f\';\n            if (value.includes(\'\u524d\u7aef\')) return \'\U0001f3a8\';\n            if (value.includes(\'\u540e\u7aef\')) return \'\u2699\ufe0f\';\n            if (value.includes(\'\u4ea7\u54c1\')) return \'\U0001f4cb\';\n            if (value.includes(\'\u6d4b\u8bd5\')) return \'\U0001f9ea\';\n            return \'\U0001f916\';\n        }\n\n        function toggleCode() {\n            setDisplay(\'join-code-box\', !isShown(\'join-code-box\'), \'block\');\n        }\n\n        function copyInvite() {\n            if (!requireAuth(\'\u8bf7\u5148\u767b\u5f55\u540e\u590d\u5236\u9080\u8bf7\u7801\')) return;\n            const code = document.getElementById(\'detail-invite-code\').textContent;\n            navigator.clipboard.writeText(code)\n                .then(() => showFeedback(\'\u9080\u8bf7\u7801\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f\', \'success\'))\n                .catch(() => showFeedback(\'\u590d\u5236\u5931\u8d25\uff0c\u8bf7\u624b\u52a8\u590d\u5236\u9080\u8bf7\u7801\', \'danger\'));\n        }\n\n        async function verifySessionOnInit() {\n            resetMeetingView();\n            try {\n                const res = await fetch(`${API_BASE}/api/auth/me`, {\n                    headers: {\'Authorization\': `Bearer ${token}`}\n                });\n                if (res.status === 200) {\n                    currentUser = await res.json();\n                    await loadMeetings();\n                    return;\n                }\n            } catch (error) {\n                showFeedback(\'\u4f1a\u8bdd\u9a8c\u8bc1\u5931\u8d25\uff0c\u8bf7\u5237\u65b0\u9875\u9762\u91cd\u8bd5\', \'warning\');\n            }\n            logout();\n        }\n\n        verifySessionOnInit();\n    </script>\n</body>\n</html>\n',
}

app = Flask(__name__, static_folder=None)
CORS(app)

SECRET_KEY = "openclaw-meeting-secret-2024"


def render_html_page(page_name):
    return Response(EMBEDDED_HTML[page_name], mimetype="text/html; charset=utf-8")


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
    return {
        "status": "ok",
        "cwd": str(Path.cwd()),
        "base_dir": str(BASE_DIR),
        "version": VERSION_TAG,
        "embedded_pages": sorted(EMBEDDED_HTML.keys()),
        "embedded_page_count": len(EMBEDDED_HTML),
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
        "embedded_pages": sorted(EMBEDDED_HTML.keys()),
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
    print(f"Starting {VERSION_TAG} Meeting Server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
