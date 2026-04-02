const assert = require('assert/strict');
const { spawn } = require('child_process');
const path = require('path');

const PORT = 43123;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const SERVER_PATH = path.join(__dirname, '..', 'server.py');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForServer() {
  let lastError;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(`${BASE_URL}/api/health`);
      if (response.ok) {
        return;
      }
      lastError = new Error(`healthcheck returned ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await sleep(500);
  }
  throw lastError || new Error('server did not start');
}

async function requestHtml(url, options = {}) {
  const response = await fetch(url, options);
  const html = await response.text();
  return { response, html };
}

async function main() {
  const server = spawn('python3', [SERVER_PATH], {
    cwd: path.join(__dirname, '..'),
    env: { ...process.env, PORT: String(PORT) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let serverOutput = '';
  server.stdout.on('data', (chunk) => {
    serverOutput += chunk.toString();
  });
  server.stderr.on('data', (chunk) => {
    serverOutput += chunk.toString();
  });

  try {
    await waitForServer();

    const unauthApp = await requestHtml(`${BASE_URL}/app`);
    assert.equal(unauthApp.response.status, 200, 'GET /app without login must return HTML');
    assert.match(unauthApp.html, /\[VER: 00:30_SELF_HEAL\]/, 'unauth HTML must expose current version');
    assert.ok(!unauthApp.html.includes('id="app-shell"'), 'unauth /app HTML must not contain app-shell');
    assert.ok(!unauthApp.html.includes("id='app-shell'"), 'unauth /app HTML must not contain app-shell');
    assert.ok(unauthApp.html.includes('id="auth-login"'), 'unauth /app must render auth DOM');

    const unauthRegister = await requestHtml(`${BASE_URL}/app?auth=register`);
    assert.equal(unauthRegister.response.status, 200, 'GET /app?auth=register must return HTML');
    assert.ok(!unauthRegister.html.includes('id="app-shell"'), 'register HTML must stay isolated from app-shell');
    assert.ok(unauthRegister.html.includes('id="auth-register"'), 'register HTML must include register form');

    const portal = await fetch(`${BASE_URL}/portal`, { redirect: 'manual' });
    assert.equal(portal.status, 302, '/portal must redirect back to /app');
    assert.equal(portal.headers.get('location'), '/app', '/portal redirect target must be /app');

    const registerResponse = await fetch(`${BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'dom-isolation@example.com',
        password: 'secret123',
        name: 'Isolation Check',
      }),
    });
    assert.equal(registerResponse.status, 201, 'register must succeed');

    const loginResponse = await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'dom-isolation@example.com',
        password: 'secret123',
      }),
    });
    assert.equal(loginResponse.status, 200, 'login must succeed');
    const cookie = loginResponse.headers.get('set-cookie');
    assert.ok(cookie, 'login must set auth cookie');

    const authApp = await requestHtml(`${BASE_URL}/app`, {
      headers: { Cookie: cookie.split(';', 1)[0] },
    });
    assert.equal(authApp.response.status, 200, 'GET /app with login must return HTML');
    assert.ok(authApp.html.includes('id="app-shell"'), 'authenticated /app HTML must contain app-shell');
    assert.ok(authApp.html.includes('[VER: 00:30_SELF_HEAL]'), 'authenticated HTML must expose current version');

    console.log('PASS verify_dom_isolation');
  } finally {
    server.kill('SIGTERM');
    await sleep(500);
    if (server.exitCode === null) {
      server.kill('SIGKILL');
    }
    if (server.exitCode && server.exitCode !== 0) {
      throw new Error(`server exited unexpectedly:\n${serverOutput}`);
    }
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
