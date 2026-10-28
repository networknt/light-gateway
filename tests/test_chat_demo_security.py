"""Browser regressions for the static chat demos (issues #258 and #259).

Run: BROWSER_BIN=/path/to/chrome python3 -m unittest discover -s tests -p test_chat_demo_security.py
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
    const payloads = [
        '<img src="missing" onerror="window.__xss = 1">',
        '<svg onload="window.__xss = 1"></svg>',
        '</strong><scr' + 'ipt>window.__xss = 1</scr' + 'ipt>',
        'plain text & < > " quotes \' and Unicode: 雪'
    ];
    function assert(condition, message) { if (!condition) throw new Error(message); }
    async function check(name, action) {
        checks.push(name);
        try { await action(); } catch (error) { failures.push(name + ': ' + error.message); }
    }
    const logElement = document.getElementById('chat-log');
    function clearLog() { logElement.replaceChildren(); }
    function assertRow(role, text) {
        const row = logElement.lastElementChild;
        assert(row !== null, 'message is missing');
        assert(row.textContent === role + ': ' + text, 'literal message text differs');
        assert(row.childNodes.length === 2, 'expected a role element and text node');
        assert(row.firstChild.tagName === 'STRONG', 'role formatting is missing');
        assert(row.firstChild.textContent === role + ':', 'role was interpreted as HTML');
        assert(row.lastChild.nodeType === Node.TEXT_NODE, 'message is not a text node');
        assert(row.querySelectorAll('img,svg,script').length === 0, 'injected markup created elements');
    }
    const settle = () => new Promise(resolve => setTimeout(resolve, 0));
    connect();
    const socket = window.__sockets.at(-1);
    for (const [index, payload] of payloads.entries()) {
        await check('WebSocket payload ' + index, () => {
            clearLog(); socket.onmessage({ data: payload }); assertRow('Assistant', payload);
        });
    }
    await check('normal role and message order', () => {
        clearLog(); socket.onmessage({ data: 'first' }); socket.onmessage({ data: 'second' });
        assert(logElement.children.length === 2, 'message count differs');
        assert(logElement.firstElementChild.textContent === 'Assistant: first', 'first message differs');
        assertRow('Assistant', 'second');
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
        assertRow('System', 'Error: ' + payloads[0]);
    });
    await check('role is also literal text', () => {
        clearLog(); log(payloads[0], 'message'); assertRow(payloads[0], 'message');
    });
    await check('close message still renders', () => {
        clearLog(); socket.close(); assertRow('System', 'Disconnected.');
    });
    if (typeof generateUUID === 'function') {
        await check('rendezvous callback response', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'success';
            socket.onopen(); await settle();
            assertRow('System', 'Backend Callback Triggered: ' + payloads[0]);
            assert(!messageInput.disabled && !sendBtn.disabled, 'successful callback did not enable sending');
        });
        await check('rendezvous callback HTTP error', async () => {
            clearLog(); window.__callbackText = payloads[1]; window.__fetchMode = 'http-error';
            socket.onopen(); await settle();
            assertRow('System', 'Error triggering backend: Error: Connect request failed: ' + payloads[1]);
        });
        await check('rendezvous callback rejected fetch', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'reject';
            socket.onopen(); await settle();
            assertRow('System', 'Error triggering backend: Error: ' + payloads[0]);
        });
    }
    await settle();
    if (window.__xss !== 0) failures.push('an injected event handler executed');
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

    def assert_demo(self, demo, expected_checks):
        page = (ROOT / 'config' / demo / 'public/index.html').read_text()
        # Execute the actual unmodified application script with browser APIs mocked.
        page = page.replace('<script>', '<script>' + MOCKS + '</script><script>', 1)
        page = page.replace('</body>', '<script>' + CHECKS + '</script></body>', 1)
        with tempfile.TemporaryDirectory(prefix='chat-demo-security-') as directory:
            fixture = Path(directory) / 'index.html'
            fixture.write_text(page)
            command = [self.browser, '--headless', '--no-sandbox', '--disable-gpu',
                       '--disable-background-networking', '--no-first-run',
                       '--user-data-dir=' + str(Path(directory) / 'profile'),
                       '--virtual-time-budget=1000', '--dump-dom', fixture.as_uri()]
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
        self.assertEqual(len(report['checks']), expected_checks, report)
        self.assertEqual(report['failures'], [], report)
        print(demo + ': ' + str(len(report['checks'])) + ' browser checks passed')

    def test_gateway(self):
        self.assert_demo('llmchat-gateway', 10)

    def test_rendezvous(self):
        self.assert_demo('llmchat-rendezvous', 13)


if __name__ == '__main__':
    unittest.main()
