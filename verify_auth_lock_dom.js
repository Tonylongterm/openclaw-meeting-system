const fs = require('fs');
const path = require('path');
const {JSDOM} = require('jsdom');

async function main() {
    const htmlPath = path.join(__dirname, 'static', 'app.html');
    const html = fs.readFileSync(htmlPath, 'utf8');
    const dom = new JSDOM(html, {
        url: 'http://localhost/app?auth=register',
        runScripts: 'dangerously',
        resources: 'usable',
        pretendToBeVisual: true,
        beforeParse(window) {
            window.fetch = async () => ({
                ok: false,
                status: 500,
                json: async () => ({})
            });
            window.EventSource = function MockEventSource() {};
            window.navigator.clipboard = {
                writeText: async () => undefined
            };
        }
    });

    await new Promise((resolve) => {
        dom.window.addEventListener('load', () => {
            dom.window.setTimeout(resolve, 0);
        });
    });

    const {document} = dom.window;
    const elementCount = document.body.querySelectorAll('*').length;
    const ids = Array.from(document.body.querySelectorAll('[id]')).map((node) => node.id);

    console.log(JSON.stringify({
        url: dom.window.location.href,
        elementCount,
        bodyChildren: Array.from(document.body.children).map((node) => node.tagName.toLowerCase()),
        ids
    }, null, 2));

    if (elementCount > 10) {
        console.error(`FAIL: auth init lock left ${elementCount} DOM elements, expected <= 10`);
        process.exit(1);
    }

    console.log('PASS: auth init lock removed all non-auth DOM nodes');
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
