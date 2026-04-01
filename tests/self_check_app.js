const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { JSDOM } = require('jsdom');

async function main() {
    const htmlPath = path.join(__dirname, '..', 'static', 'app.html');
    const html = fs.readFileSync(htmlPath, 'utf8');

    const dom = new JSDOM(html, {
        runScripts: 'dangerously',
        resources: 'usable',
        url: 'http://localhost/app?auth=login',
        pretendToBeVisual: true,
        beforeParse(window) {
            window.fetch = async () => ({ ok: false, status: 401, json: async () => ({}) });
            window.EventSource = function EventSource() {
                throw new Error('EventSource should not be constructed without a token');
            };
            window.navigator.clipboard = {
                writeText: async () => undefined,
            };
            window.requestAnimationFrame = (cb) => setTimeout(() => cb(Date.now()), 0);
            window.cancelAnimationFrame = (id) => clearTimeout(id);
            window.localStorage.removeItem('token');
        },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const { document, localStorage } = dom.window;
    assert.strictEqual(localStorage.getItem('token'), null, 'token must be empty');
    assert.strictEqual(document.getElementById('modal-create'), null, 'modal-create must not exist without token');

    console.log('PASSED: unauthenticated app HTML does not expose modal-create');
    dom.window.close();
}

main().catch((error) => {
    console.error(`FAILED: ${error.message}`);
    process.exitCode = 1;
});
