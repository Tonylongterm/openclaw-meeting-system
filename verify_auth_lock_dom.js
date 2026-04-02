const { JSDOM } = require('jsdom');

async function testNoTokenAccess() {
    const url = 'http://localhost:7788/portal?auth=register';
    console.log(`Testing access to ${url} without token...`);

    try {
        const response = await fetch(url);
        const html = await response.text();
        const dom = new JSDOM(html);
        const document = dom.window.document;

        // 验证标题
        console.log('Document Title:', document.title);
        
        // 核心检查：是否包含控制台特有的 ID 或元素
        const appShell = document.getElementById('app-shell');
        const meetingGrid = document.getElementById('meeting-grid');
        const streamFlow = document.getElementById('stream-flow');

        console.log('Checking for console elements...');
        let leaked = false;
        if (appShell) { console.error('FAILED: Found #app-shell'); leaked = true; }
        if (meetingGrid) { console.error('FAILED: Found #meeting-grid'); leaked = true; }
        if (streamFlow) { console.error('FAILED: Found #stream-flow'); leaked = true; }

        if (!leaked) {
            console.log('SUCCESS: DOM structure is clean. No console elements found.');
        } else {
            process.exit(1);
        }

    } catch (error) {
        console.error('Test failed due to network or server error:', error.message);
        process.exit(1);
    }
}

testNoTokenAccess();
