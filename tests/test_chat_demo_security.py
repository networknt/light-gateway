"""Browser regressions for the static chat demos (issues #258 and #259).

Run: BROWSER_BIN=/path/to/chrome python3 -B -m unittest discover -s tests -p test_chat_demo_security.py
The browser sandbox stays enabled by default. BROWSER_NO_SANDBOX=1 is an explicit
opt-in only for disposable CI/container environments that cannot support it.
Only the demo JavaScript runs; WebSocket/fetch are mocked and no Gateway is started.
"""
import html
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEMOS = {
    'llmchat-gateway': {'streaming': False, 'rendezvous': False},
    'llmchat-rendezvous': {'streaming': False, 'rendezvous': True},
    'ai-gateway': {'streaming': True, 'rendezvous': False},
}
PAYLOADS = [
    '<img src="missing" onerror="window.__xss = 1">',
    '<svg onload="window.__xss = 1"></svg>',
    '</strong><script>window.__xss = 1</script>',
    '<details open ontoggle="window.__xss = 1">nested</details>',
    '<video src="missing" onerror="window.__xss = 1"></video>',
    'plain text & < > " quotes and Unicode: 雪',
]
COMMON_CHECKS = {
    'normal role and message order', 'user send preserves raw wire text',
    'Enter sends literal user text', 'WebSocket error text', 'role is also literal text',
    'close message still renders', 'query values stay separate',
    'structural detector rejects arbitrary elements',
} | {'WebSocket payload ' + str(index) for index in range(len(PAYLOADS))}
CALLBACK_CHECKS = {
    'rendezvous callback response', 'rendezvous callback HTTP error',
    'rendezvous callback rejected fetch',
}
MOCKS = r"""
window.__xss = 0;
window.__sockets = [];
window.__fetchMode = 'success';
window.__callbackText = '';
window.WebSocket = class {
    constructor(url) { this.url = url; this.sent = []; window.__sockets.push(this); }
    send(text) { this.sent.push(text); }
    close() { this.onclose?.(); }
};
window.fetch = () => window.__fetchMode === 'reject'
    ? Promise.reject(new Error(window.__callbackText))
    : Promise.resolve({ ok: window.__fetchMode === 'success',
        statusText: window.__callbackText, text: () => Promise.resolve(window.__callbackText) });
"""
CHECKS = r"""
(async () => {
    const failures = [];
    const checks = [];
    const mode = window.__demo;
    const payloads = mode.payloads;
    function assert(condition, message) { if (!condition) throw new Error(message); }
    async function check(name, action) {
        checks.push(name);
        try { await action(); } catch (error) { failures.push(name + ': ' + error.message); }
    }
    const logElement = document.getElementById('chat-log');
    function clearLog() {
        logElement.replaceChildren();
        if (mode.streaming) currentAssistantMsgDiv = null;
    }
    function assertRow(role, text) {
        const row = logElement.lastElementChild;
        assert(row !== null, 'message is missing');
        assert(row.textContent === role + ': ' + text, 'literal message text differs');
        // Only one element (the fixed strong label) is allowed. Every other node,
        // including every child of the label, must be text. This rejects ANY injected
        // tag/attribute synchronously; security does not depend on event timing.
        assert(row.firstChild.tagName === 'STRONG', 'role formatting is missing');
        assert(row.firstChild.textContent === role + ':', 'role was interpreted as HTML');
        assert(row.children.length === 1, 'unexpected message element');
        assert(row.getAttributeNames().every(name => name === 'class'), 'unexpected row attribute');
        assert(row.firstChild.getAttributeNames().length === 0, 'unexpected label attribute');
        assert(Array.from(row.firstChild.childNodes).every(node => node.nodeType === Node.TEXT_NODE),
            'unexpected label element');
        assert(Array.from(row.childNodes).slice(1).every(node => node.nodeType === Node.TEXT_NODE),
            'unexpected message markup');
    }
    async function until(condition) {
        for (let attempt = 0; attempt < 100; attempt++) {
            if (condition()) return;
            await new Promise(resolve => setTimeout(resolve, 5));
        }
        throw new Error('callback did not complete');
    }
    connect();
    let socket = window.__sockets.at(-1);
    await check('query values stay separate', () => {
        const user = 'user&model=override#fragment +雪';
        const model = 'model?x=1&channelId=override#fragment +雪';
        document.getElementById('userId').value = user;
        document.getElementById('model').value = model;
        if (mode.streaming) sessionStorage.setItem('sessionId', 'session&extra=value#fragment +雪');
        connect(); socket = window.__sockets.at(-1);
        const query = new URLSearchParams(socket.url.split('?')[1].split('#')[0]);
        assert(query.get('userId') === user, 'userId escaped its query value');
        assert(query.get('model') === model, 'model escaped its query value');
        const expectedKeys = ['userId', 'model'];
        if (mode.rendezvous) {
            expectedKeys.push('channelId');
            assert(query.get('channelId') !== 'override', 'model overwrote channelId');
        }
        if (mode.streaming) {
            expectedKeys.push('sessionId');
            assert(query.get('sessionId') === sessionStorage.getItem('sessionId'), 'sessionId escaped its query value');
        }
        assert(JSON.stringify(Array.from(query.keys()).sort()) === JSON.stringify(expectedKeys.sort()),
            'unexpected or duplicate query key');
    });
    for (const [index, payload] of payloads.entries()) {
        await check('WebSocket payload ' + index, () => {
            clearLog(); socket.onmessage({ data: payload }); assertRow('Assistant', payload);
        });
    }
    await check('normal role and message order', () => {
        clearLog(); socket.onmessage({ data: 'first' }); socket.onmessage({ data: 'second' });
        if (mode.streaming) {
            assert(logElement.children.length === 1, 'chunks did not share one row');
            assertRow('Assistant', 'firstsecond');
        } else {
            assert(logElement.children.length === 2, 'message count differs');
            assert(logElement.firstElementChild.textContent === 'Assistant: first', 'first message differs');
            assertRow('Assistant', 'second');
        }
        assert(logElement.lastElementChild.className === 'message assistant', 'role class differs');
    });
    await check('user send preserves raw wire text', () => {
        clearLog(); messageInput.value = payloads[0]; sendMessage();
        assertRow('User', payloads[0]);
        assert(socket.sent.at(-1) === payloads[0], 'wire payload was HTML-encoded');
        assert(messageInput.value === '', 'input was not cleared');
    });
    await check('Enter sends literal user text', () => {
        clearLog(); messageInput.value = payloads[1];
        messageInput.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter' }));
        assertRow('User', payloads[1]); assert(socket.sent.at(-1) === payloads[1], 'Enter payload differs');
    });
    await check('WebSocket error text', () => {
        clearLog(); socket.onerror({ toString: () => payloads[0] });
        assertRow('System', mode.streaming ? 'Error encountered. Check console.' : 'Error: ' + payloads[0]);
    });
    await check('role is also literal text', () => {
        clearLog(); log(payloads[0], 'message'); assertRow(payloads[0], 'message');
    });
    await check('close message still renders', () => {
        clearLog(); socket.close(); assertRow('System', 'Disconnected.');
    });
    if (mode.rendezvous) {
        await check('rendezvous callback response', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'success';
            socket.onopen();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Backend Callback Triggered: ' + payloads[0]);
            assert(!messageInput.disabled && !sendBtn.disabled, 'successful callback did not enable sending');
        });
        await check('rendezvous callback HTTP error', async () => {
            clearLog(); window.__callbackText = payloads[1]; window.__fetchMode = 'http-error';
            socket.onopen();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Error triggering backend: Error: Connect request failed: ' + payloads[1]);
        });
        await check('rendezvous callback rejected fetch', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'reject';
            socket.onopen();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Error triggering backend: Error: ' + payloads[0]);
        });
    }
    if (mode.streaming) {
        await check('session info renders literally', () => {
            clearLog();
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: payloads[0] }) });
            assertRow('System', 'Session initialized: ' + payloads[0]);
            assert(sessionStorage.getItem('sessionId') === payloads[0], 'session ID differs');
        });
    }
    await check('structural detector rejects arbitrary elements', () => {
        for (const tag of ['details', 'video', 'iframe']) {
            clearLog(); log('Assistant', 'message');
            logElement.lastElementChild.appendChild(document.createElement(tag));
            let rejected = false;
            try { assertRow('Assistant', 'message'); } catch { rejected = true; }
            assert(rejected, 'detector accepted injected ' + tag);
        }
        clearLog();
    });
    const result = document.createElement('pre');
    result.id = 'chat-security-test-result';
    result.textContent = JSON.stringify({ checks, failures });
    document.body.appendChild(result);
})().catch(error => { document.body.textContent = 'Harness failed: ' + error.message; });
"""


class ChatDemoSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.browser = os.environ.get('BROWSER_BIN') or shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.browser:
            raise RuntimeError('Set BROWSER_BIN to a Chromium/Chrome executable; browser tests must not be skipped')

    def assert_demo(self, demo):
        page = (ROOT / 'config' / demo / 'public/index.html').read_text()
        # Execute the actual unmodified application script with browser APIs mocked.
        mode = dict(DEMOS[demo], payloads=PAYLOADS)
        # Escape data for the script context, including the literal closing-script payload.
        mode_json = json.dumps(mode).replace('<', r'\u003c')
        mocks = 'window.__demo = ' + mode_json + ';' + MOCKS
        page = page.replace('<script>', '<script>' + mocks + '</script><script>', 1)
        page = page.replace('</body>', '<script>' + CHECKS + '</script></body>', 1)
        with tempfile.TemporaryDirectory(prefix='chat-demo-security-') as directory:
            fixture = Path(directory) / 'index.html'
            fixture.write_text(page)
            command = [self.browser, '--headless', '--disable-gpu',
                       '--disable-dev-shm-usage', '--disable-extensions', '--disable-sync',
                       '--no-default-browser-check',
                       '--disable-background-networking', '--no-first-run',
                       '--user-data-dir=' + str(Path(directory) / 'profile'),
                       '--virtual-time-budget=2000', '--dump-dom', fixture.as_uri()]
            if os.environ.get('BROWSER_NO_SANDBOX') == '1':
                command.insert(1, '--no-sandbox')
            # Kill the entire fixture browser group on timeout, including child processes,
            # before removing its temporary profile.
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, start_new_session=True) as browser:
                try:
                    stdout, stderr = browser.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(browser.pid, signal.SIGKILL)
                    stdout, stderr = browser.communicate()
                    self.fail('Fixture browser timed out: ' + stderr[-3000:])
        self.assertEqual(browser.returncode, 0, stderr)
        match = re.search(r'<pre id="chat-security-test-result">(.*?)</pre>', stdout, re.S)
        self.assertIsNotNone(match, 'Browser did not complete the checks: ' + stdout[-3000:])
        report = json.loads(html.unescape(match.group(1)))
        expected = set(COMMON_CHECKS)
        if DEMOS[demo]['rendezvous']:
            expected |= CALLBACK_CHECKS
        if DEMOS[demo]['streaming']:
            expected.add('session info renders literally')
        self.assertTrue(expected.issubset(report['checks']), report)
        self.assertEqual(len(report['checks']), len(set(report['checks'])), 'duplicate check names')
        self.assertEqual(report['failures'], [], report)
        print(demo + ': ' + str(len(report['checks'])) + ' browser checks passed')

    def test_gateway(self):
        self.assert_demo('llmchat-gateway')

    def test_ai_gateway(self):
        self.assert_demo('ai-gateway')

    def test_rendezvous(self):
        self.assert_demo('llmchat-rendezvous')


if __name__ == '__main__':
    unittest.main()
