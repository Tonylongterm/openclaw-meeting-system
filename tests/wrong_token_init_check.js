const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function extractInlineScript() {
  const serverPath = path.join(__dirname, '..', 'server.py');
  const source = fs.readFileSync(serverPath, 'utf8');
  const htmlMatch = source.match(/APP_HTML = '''([\s\S]*?)'''\n\nINLINE_APP_HTML = APP_HTML/);
  assert(htmlMatch, 'Failed to extract inline APP_HTML from server.py');
  const scriptMatch = htmlMatch[1].match(/<script>([\s\S]*?)<\/script>/);
  assert(scriptMatch, 'Failed to extract inline script from APP_HTML');
  return scriptMatch[1];
}

class ClassList {
  constructor(initial = []) {
    this.set = new Set(initial);
  }

  add(...names) {
    names.forEach((name) => this.set.add(name));
  }

  remove(...names) {
    names.forEach((name) => this.set.delete(name));
  }

  toggle(name, force) {
    if (force === true) {
      this.set.add(name);
      return true;
    }
    if (force === false) {
      this.set.delete(name);
      return false;
    }
    if (this.set.has(name)) {
      this.set.delete(name);
      return false;
    }
    this.set.add(name);
    return true;
  }

  contains(name) {
    return this.set.has(name);
  }
}

class MockElement {
  constructor(id = '', classNames = [], tagName = 'div') {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.classList = new ClassList(classNames);
    this.style = {display: ''};
    this.dataset = {};
    this.children = [];
    this.value = '';
    this.textContent = '';
    this.innerHTML = '';
    this.onclick = null;
    this.parentNode = null;
    this.nextSibling = null;
    this.isConnected = true;
    this.scrollTop = 0;
    this.scrollHeight = 0;
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  remove() {
    this.isConnected = false;
  }
}

function createDocument() {
  const elementsById = new Map();
  const allElements = [];

  function register(id, classes = [], extra = {}) {
    const element = new MockElement(id, classes, extra.tagName);
    Object.assign(element, extra);
    if (id) elementsById.set(id, element);
    allElements.push(element);
    return element;
  }

  const ids = [
    'auth-shell', 'app-shell', 'page-auth', 'page-list', 'page-detail',
    'auth-feedback', 'auth-login', 'auth-register', 'login-email', 'login-password',
    'reg-name', 'reg-email', 'reg-password', 'meeting-grid', 'display-user-name',
    'detail-title', 'detail-invite-code', 'set-topic', 'set-rounds', 'set-host',
    'agent-list', 'agent-count', 'stream-flow', 'new-title', 'new-topic',
    'new-rounds', 'btn-start-meeting', 'meeting-running-hint', 'meeting-finished-hint',
    'modal-create', 'global-feedback', 'join-code-box'
  ];

  ids.forEach((id) => register(id));

  elementsById.get('auth-shell').classList.add('shell');
  elementsById.get('app-shell').classList.add('shell');
  elementsById.get('page-auth').classList.add('page');
  elementsById.get('page-list').classList.add('page');
  elementsById.get('page-detail').classList.add('page');
  elementsById.get('auth-login').classList.add('auth-form');
  elementsById.get('auth-register').classList.add('auth-form', 'hidden');
  elementsById.get('modal-create').classList.add('hidden');
  elementsById.get('global-feedback').classList.add('hidden');
  elementsById.get('join-code-box').classList.add('hidden');
  elementsById.get('meeting-running-hint').classList.add('hidden');
  elementsById.get('meeting-finished-hint').classList.add('hidden');

  const authTabLogin = register('', ['auth-tab', 'active']);
  authTabLogin.dataset.authTab = 'login';
  const authTabRegister = register('', ['auth-tab']);
  authTabRegister.dataset.authTab = 'register';
  const invitePlaceholder = register('', ['invite-placeholder']);
  invitePlaceholder.textContent = '...';

  const body = new MockElement('body');

  return {
    body,
    createElement(tagName) {
      return new MockElement('', [], tagName);
    },
    getElementById(id) {
      return elementsById.get(id) || null;
    },
    querySelectorAll(selector) {
      if (!selector.startsWith('.')) return [];
      const className = selector.slice(1);
      return allElements.filter((element) => element.classList.contains(className));
    }
  };
}

async function flushAsyncWork() {
  for (let i = 0; i < 5; i += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
}

async function main() {
  const script = extractInlineScript();
  const document = createDocument();
  const fetchCalls = [];
  let loadMeetingsCalls = 0;

  const localStorageState = new Map([['token', 'wrong-token']]);
  const localStorage = {
    getItem(key) {
      return localStorageState.has(key) ? localStorageState.get(key) : null;
    },
    setItem(key, value) {
      localStorageState.set(key, String(value));
    },
    removeItem(key) {
      localStorageState.delete(key);
    }
  };

  const location = {
    origin: 'https://example.com',
    href: 'https://example.com/app?auth=register',
    search: '?auth=register',
    hash: '#register'
  };

  const context = vm.createContext({
    console,
    document,
    localStorage,
    navigator: {
      clipboard: {
        writeText: () => Promise.resolve()
      }
    },
    EventSource: class {
      constructor() {}
      close() {}
    },
    fetch: async (url, options = {}) => {
      fetchCalls.push({url, options});
      if (String(url).endsWith('/api/auth/me')) {
        return {
          status: 401,
          ok: false,
          async json() {
            return {message: 'Token is invalid'};
          }
        };
      }
      throw new Error(`Unexpected fetch call: ${url}`);
    },
    window: {
      location,
      history: {
        replaceState(_state, _title, nextUrl) {
          const url = typeof nextUrl === 'string' ? new URL(nextUrl, location.origin) : nextUrl;
          location.href = url.toString();
          location.search = url.search;
          location.hash = url.hash;
        }
      },
      addEventListener() {},
      __APP_TEST_HOOKS__: {
        onLoadMeetingsCalled() {
          loadMeetingsCalls += 1;
        }
      }
    },
    URL,
    URLSearchParams,
    setTimeout,
    clearTimeout,
    Promise
  });

  vm.runInContext(script, context, {filename: 'inline-app.js'});
  await flushAsyncWork();

  const authShell = document.getElementById('auth-shell');
  const authPage = document.getElementById('page-auth');
  const appShell = document.getElementById('app-shell');

  assert.equal(loadMeetingsCalls, 0, 'loadMeetings should not be called for wrong-token');
  assert.equal(fetchCalls.length, 1, 'init should only call /api/auth/me once');
  assert.equal(fetchCalls[0].url, 'https://example.com/api/auth/me');
  assert.equal(localStorage.getItem('token'), null, 'invalid token should be removed from localStorage');
  assert.equal(authShell.classList.contains('active'), true, 'auth shell should be visible');
  assert.equal(authPage.classList.contains('active'), true, 'login page should stay active');
  assert.equal(appShell.classList.contains('active'), false, 'app shell must stay hidden');
  assert.equal(document.getElementById('auth-login').style.display, 'flex', 'login form should be shown');
  assert.equal(document.getElementById('auth-register').style.display, 'none', 'register form should be hidden');

  console.log('wrong-token init check passed');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
