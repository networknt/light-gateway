"""Browser regressions for static chat rendering, session lifetime and channel IDs.

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
    'k8s-ai-gateway': {'streaming': True, 'rendezvous': False},
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
    'native secure channel is shared with callback but not logged',
    'getRandomValues creates UUID v4 channel without native UUID',
    'missing or failing crypto prevents socket and callback',
    'replaced rendezvous sockets and late callbacks cannot affect the current connection',
}
MOCKS = r"""
window.__xss = 0;
window.__sockets = [];
window.__fetchMode = 'success';
window.__callbackText = '';
window.__fetches = [];
window.__storageWrites = [];
window.__consoleLogs = [];
console.log = (...args) => window.__consoleLogs.push(args.join(' '));
window.__legacyLocalStorage = localStorage;
window.__legacyStorage = sessionStorage;
window.__legacyStorage.setItem('sessionId', 'legacy-session-canary');
window.__legacyLocalStorage.setItem('sessionId', 'legacy-local-canary');
window.__pendingFetches = [];
window.__fetchOptions = [];
const originalSetItem = Storage.prototype.setItem;
Storage.prototype.setItem = function(key, value) {
    window.__storageWrites.push({ key, value });
    return originalSetItem.call(this, key, value);
};
if (window.__demo.storageBlocked) {
    for (const name of ['sessionStorage', 'localStorage']) {
        Object.defineProperty(window, name, { configurable: true, get() { throw new Error('Storage is blocked'); } });
    }
}
window.WebSocket = class {
    static CONNECTING = 0; static OPEN = 1; static CLOSING = 2; static CLOSED = 3;
    constructor(url) { this.url = url; this.sent = []; this.readyState = WebSocket.CONNECTING; window.__sockets.push(this); }
    open() {
        if (this.readyState !== WebSocket.CONNECTING) return;
        this.readyState = WebSocket.OPEN; this.onopen?.();
    }
    send(text) {
        if (this.readyState !== WebSocket.OPEN) throw new Error('Socket is not open');
        this.sent.push(text);
    }
    close() {
        if (this.readyState >= WebSocket.CLOSING) return;
        this.readyState = WebSocket.CLOSING;
        setTimeout(() => { this.readyState = WebSocket.CLOSED; this.onclose?.(); }, 0);
    }
};
window.fetch = (url, options) => {
    window.__fetches.push(url); window.__fetchOptions.push(options);
    if (window.__fetchMode === 'deferred') {
        // Resolve after abort/replacement to exercise already-in-flight completion races.
        return new Promise((resolve, reject) => window.__pendingFetches.push({ resolve, reject }));
    }
    return window.__fetchMode === 'reject'
        ? Promise.reject(new Error(window.__callbackText))
        : Promise.resolve({ ok: window.__fetchMode === 'success',
            statusText: window.__callbackText, text: () => Promise.resolve(window.__callbackText) });
};
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
    async function openSocket(socket) {
        window.__fetchMode = 'success'; window.__callbackText = 'ready';
        socket.open();
        if (mode.rendezvous) await until(() => !sendBtn.disabled);
    }
    connect();
    let socket = window.__sockets.at(-1);
    await check('query values stay separate', async () => {
        const user = 'user&model=override#fragment +雪';
        const model = 'model?x=1&channelId=override#fragment +雪';
        document.getElementById('userId').value = user;
        document.getElementById('model').value = model;
        connect(); socket = window.__sockets.at(-1);
        await openSocket(socket);
        if (mode.streaming) {
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: 'session&extra=value#fragment +雪' }) });
            connect(); socket = window.__sockets.at(-1);
            await openSocket(socket);
        }
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
            assert(query.get('sessionId') === 'session&extra=value#fragment +雪', 'sessionId escaped its query value');
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
    await check('close message still renders', async () => {
        clearLog(); socket.close();
        assert(socket.readyState === WebSocket.CLOSING, 'close event was synchronous');
        await until(() => socket.readyState === WebSocket.CLOSED);
        assertRow('System', 'Disconnected.');
    });
    if (mode.rendezvous) {
        await check('rendezvous callback response', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'success';
            connect(); socket = window.__sockets.at(-1); socket.open();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Backend Callback Triggered: ' + payloads[0]);
            assert(!messageInput.disabled && !sendBtn.disabled, 'successful callback did not enable sending');
        });
        await check('rendezvous callback HTTP error', async () => {
            clearLog(); window.__callbackText = payloads[1]; window.__fetchMode = 'http-error';
            connect(); socket = window.__sockets.at(-1); socket.open();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Error triggering backend: Error: Connect request failed: ' + payloads[1]);
        });
        await check('rendezvous callback rejected fetch', async () => {
            clearLog(); window.__callbackText = payloads[0]; window.__fetchMode = 'reject';
            connect(); socket = window.__sockets.at(-1); socket.open();
            await until(() => logElement.lastElementChild?.textContent.startsWith('System: Backend Callback Triggered:')
                || logElement.lastElementChild?.textContent.startsWith('System: Error triggering backend:'));
            assertRow('System', 'Error triggering backend: Error: ' + payloads[0]);
        });
    }
    if (mode.streaming) {
        await check('fresh page ignores persisted session', () => {
            assert(!new URL(window.__sockets[0].url).searchParams.has('sessionId'), 'legacy session was resumed');
            if (!mode.storageBlocked) {
                assert(window.__legacyStorage.getItem('sessionId') === null, 'legacy session value was not removed');
                assert(window.__legacyLocalStorage.getItem('sessionId') === null, 'legacy local value was not removed');
            }
        });
        await check('session IDs stay out of storage and logs', async () => {
            connect(); socket = window.__sockets.at(-1); await openSocket(socket);
            clearLog();
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: 'session-secret-canary' }) });
            assertRow('System', 'Session initialized.');
            assert(!logElement.textContent.includes('session-secret-canary'), 'session ID was displayed');
            assert(window.__storageWrites.length === 0, 'page wrote to browser storage');
            for (const storage of [window.__legacyStorage, window.__legacyLocalStorage]) {
                for (let index = 0; index < storage.length; index++) {
                    assert(storage.getItem(storage.key(index)) !== 'session-secret-canary', 'session ID persisted in browser storage');
                }
            }
            assert(!window.__consoleLogs.some(line => line.includes('session-secret-canary')), 'session ID was printed');
            connect(); socket = window.__sockets.at(-1);
            assert(new URL(socket.url).searchParams.get('sessionId') === 'session-secret-canary', 'same-context reconnect lost memory ID');
        });
        await check('changed context and stale sockets cannot reuse a session', async () => {
            const stale = socket;
            document.getElementById('userId').value = 'different-user';
            connect(); socket = window.__sockets.at(-1);
            assert(!new URL(socket.url).searchParams.has('sessionId'), 'changed user reused session');
            await openSocket(socket);
            stale.onmessage({ data: JSON.stringify({ type: 'session', sessionId: 'stale-session-canary' }) });
            await until(() => stale.readyState === WebSocket.CLOSED);
            assert(!messageInput.disabled, 'stale close disabled current connection');
            connect(); socket = window.__sockets.at(-1);
            assert(!new URL(socket.url).searchParams.has('sessionId'), 'stale socket replaced current session');
            await openSocket(socket);
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: 'model-session-canary' }) });
            document.getElementById('model').value = 'different-model';
            connect(); socket = window.__sockets.at(-1);
            assert(!new URL(socket.url).searchParams.has('sessionId'), 'changed model reused session');
        });
        await check('invalid session response is not retained', async () => {
            await openSocket(socket);
            clearLog();
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: 'previous-valid-session' }) });
            clearLog();
            socket.onmessage({ data: JSON.stringify({ type: 'session', sessionId: { invalid: true } }) });
            assertRow('System', 'Invalid session response.');
            connect(); socket = window.__sockets.at(-1);
            assert(!new URL(socket.url).searchParams.has('sessionId'), 'invalid session was retained');
        });
    }
    if (mode.streaming) {
        await check('replacement resets stream and prevents sends while connecting', async () => {
            await openSocket(socket); clearLog();
            socket.onmessage({ data: 'old-stream' });
            const oldRow = logElement.lastElementChild, stale = socket;
            connect(); socket = window.__sockets.at(-1);
            assert(stale.readyState === WebSocket.CLOSING, 'previous socket was not closed asynchronously');
            assert(messageInput.disabled && sendBtn.disabled, 'sending remained enabled during connect');
            messageInput.value = 'retained draft'; sendMessage();
            assert(socket.sent.length === 0 && messageInput.value === 'retained draft', 'sent or lost draft before OPEN');
            await openSocket(socket);
            await until(() => stale.readyState === WebSocket.CLOSED);
            assert(!messageInput.disabled && !sendBtn.disabled, 'late close disabled current socket');
            stale.onmessage({ data: 'stale-chunk' });
            stale.onerror?.({ toString: () => 'stale-error' });
            socket.onmessage({ data: 'new-stream' });
            assert(oldRow.textContent === 'Assistant: old-stream', 'previous stream changed');
            assert(logElement.lastElementChild !== oldRow, 'new stream reused old bubble');
            assertRow('Assistant', 'new-stream');
            assert(!logElement.textContent.includes('stale-'), 'stale event was rendered');
        });
    }
    if (mode.rendezvous) {
        const originalCrypto = Object.getOwnPropertyDescriptor(window, 'crypto');
        const originalRandom = Math.random;
        function cryptoSource(value) { Object.defineProperty(window, 'crypto', { configurable: true, value }); }
        try {
            Math.random = () => { throw new Error('Weak randomness must not be used'); };
            await check('native secure channel is shared with callback but not logged', async () => {
                let calls = 0;
                const native = { randomUUID() {
                    assert(this === native, 'native crypto receiver was lost');
                    calls++;
                    return calls === 1 ? '00000000-0000-4000-8000-000000000001' : '00000000-0000-4000-8000-000000000002';
                } };
                cryptoSource(native);
                clearLog(); window.__fetchMode = 'success'; window.__callbackText = 'ok';
                connect(); socket = window.__sockets.at(-1);
                const channel = new URL(socket.url).searchParams.get('channelId');
                assert(channel === '00000000-0000-4000-8000-000000000001', 'native generator was not used');
                socket.open();
                await until(() => logElement.textContent.includes('Backend Callback Triggered: ok'));
                assert(new URL(window.__fetches.at(-1)).searchParams.get('channelId') === channel, 'callback channel differs');
                assert(!logElement.textContent.includes(channel), 'channel ID was displayed');
                assert(!window.__consoleLogs.some(line => line.includes(channel)), 'channel URL was printed');
                connect(); socket = window.__sockets.at(-1);
                assert(new URL(socket.url).searchParams.get('channelId') !== channel, 'channel reused across connections');
                assert(calls === 2, 'generator call count differs');
            });
            await check('getRandomValues creates UUID v4 channel without native UUID', () => {
                const source = { getRandomValues(bytes) {
                    assert(this === source && bytes.length === 16, 'invalid cryptographic byte request');
                    bytes.fill(255); return bytes;
                } };
                cryptoSource(source);
                connect(); socket = window.__sockets.at(-1);
                assert(new URL(socket.url).searchParams.get('channelId') === 'ffffffff-ffff-4fff-bfff-ffffffffffff', 'UUID bits or byte source differ');
            });
            await check('missing or failing crypto prevents socket and callback', () => {
                for (const source of [undefined, {}, { randomUUID() { throw new Error('provider failure'); } },
                    { getRandomValues() { throw new Error('provider failure'); } }]) {
                    cryptoSource(source); clearLog();
                    const sockets = window.__sockets.length, fetches = window.__fetches.length;
                    connect();
                    assert(window.__sockets.length === sockets && window.__fetches.length === fetches, 'insecure connection was attempted');
                    assertRow('System', 'Secure channel ID generation is unavailable.');
                }
            });
        } finally {
            Math.random = originalRandom;
            if (originalCrypto) Object.defineProperty(window, 'crypto', originalCrypto);
            else delete window.crypto;
        }
    }
    if (mode.rendezvous) {
        await check('replaced rendezvous sockets and late callbacks cannot affect the current connection', async () => {
            for (const outcome of ['resolve', 'reject']) {
                window.__fetchMode = 'deferred'; clearLog();
                connect(); const stale = window.__sockets.at(-1); stale.open();
                const oldCallback = window.__pendingFetches.at(-1), oldSignal = window.__fetchOptions.at(-1).signal;
                connect(); socket = window.__sockets.at(-1);
                assert(stale.readyState === WebSocket.CLOSING && oldSignal.aborted, 'old connection/callback was not cancelled');
                socket.open();
                assert(sendBtn.disabled && messageInput.disabled, 'sending enabled before callback admission');
                messageInput.value = 'waiting draft'; sendMessage();
                assert(socket.sent.length === 0 && messageInput.value === 'waiting draft', 'sent before callback admission');
                const currentCallback = window.__pendingFetches.at(-1);
                currentCallback.resolve({ ok: true, text: () => Promise.resolve('current-callback') });
                await until(() => !sendBtn.disabled);
                const fetches = window.__fetches.length;
                stale.onopen?.(); stale.onmessage?.({ data: 'stale-message' }); stale.onerror?.({ toString: () => 'stale-error' });
                if (outcome === 'resolve') oldCallback.resolve({ ok: true, text: () => Promise.resolve('stale-callback') });
                else oldCallback.reject(new Error('stale-callback'));
                await new Promise(resolve => setTimeout(resolve, 10));
                assert(stale.readyState === WebSocket.CLOSED, 'old close did not finish');
                assert(window.__fetches.length === fetches, 'stale open triggered a callback');
                assert(!sendBtn.disabled && !messageInput.disabled, 'stale completion disabled active controls');
                assert(!logElement.textContent.includes('stale-'), 'stale completion was rendered');
            }
            window.__fetchMode = 'success';
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


def configmap_page():
    lines = (ROOT / 'k8s/light-gateway/public-configmap.yaml').read_text().splitlines()
    start = lines.index('  index.html: |') + 1
    body = []
    for line in lines[start:]:
        if line.strip() and not line.startswith('    '):
            break
        body.append(line[4:] if line.startswith('    ') else '')
    return '\n'.join(body) + '\n'


class ChatDemoSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.browser = os.environ.get('BROWSER_BIN') or shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.browser:
            raise RuntimeError('Set BROWSER_BIN to a Chromium/Chrome executable; browser tests must not be skipped')

    def assert_demo(self, demo, storage_blocked=False):
        page = configmap_page() if demo == 'k8s-ai-gateway' else (ROOT / 'config' / demo / 'public/index.html').read_text()
        # Execute the actual unmodified application script with browser APIs mocked.
        mode = dict(DEMOS[demo], payloads=PAYLOADS, storageBlocked=storage_blocked)
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
            expected |= {'fresh page ignores persisted session', 'session IDs stay out of storage and logs',
                         'changed context and stale sockets cannot reuse a session', 'invalid session response is not retained',
                         'replacement resets stream and prevents sends while connecting'}
        self.assertTrue(expected.issubset(report['checks']), report)
        self.assertEqual(len(report['checks']), len(set(report['checks'])), 'duplicate check names')
        self.assertEqual(report['failures'], [], report)
        print(demo + ': ' + str(len(report['checks'])) + ' browser checks passed')

    def test_gateway(self):
        self.assert_demo('llmchat-gateway')

    def test_ai_gateway(self):
        self.assert_demo('ai-gateway')

    def test_ai_gateway_storage_unavailable(self):
        self.assert_demo('ai-gateway', storage_blocked=True)

    def test_kubernetes_page_matches_canonical(self):
        self.assertEqual(configmap_page(), (ROOT / 'config/ai-gateway/public/index.html').read_text())

    def test_kubernetes_ai_gateway(self):
        self.assert_demo('k8s-ai-gateway')

    def test_kubernetes_ai_gateway_storage_unavailable(self):
        self.assert_demo('k8s-ai-gateway', storage_blocked=True)

    def test_rendezvous(self):
        self.assert_demo('llmchat-rendezvous')


if __name__ == '__main__':
    unittest.main()
