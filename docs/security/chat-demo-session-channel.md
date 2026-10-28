# Chat demo session and channel security (Checkmarx A13/A14)

These changes address the remaining non-false-positive light-gateway findings in
[the partner assessment](https://github.com/networknt/networknt-doc/blob/master/src/security/partner-checkmarx-assessment-2026-10-28.md):
A13 (worksheet row 36, ai-gateway browser session storage) and A14 (row 37,
llmchat-rendezvous channel randomness). A12's text-rendering fixes are retained.

## A13: page-memory reconnect state

The AI demo keeps its server-issued session ID only in the current page's memory.
It neither reads a reconnect ID from storage nor writes one to sessionStorage or
localStorage, and no longer displays the ID in the chat log. On startup it tries
to remove the legacy sessionId key from sessionStorage and localStorage;
storage being blocked does not prevent the demo from working. If storage is
blocked, cleanup cannot run; loading the updated page when storage is available
removes those legacy entries. No other storage keys are cleared.

Disconnect/reconnect in the same page can resume the same selected user/model.
Changing either selection discards the reconnect ID. Reloading/closing the page
loses that in-memory state and starts a new conversation. Events from a replaced
socket cannot overwrite the active session or disable its controls. Replacing a
connection resets its stream bubble and disables sending until OPEN; both the
controls and sendMessage reject sends while CONNECTING or closing. This selection
binding is client-side lifecycle hygiene, not authenticated owner verification.

Page memory is still accessible to compromised same-origin JavaScript. An ID used
as a bearer capability must not be treated as safe merely because it is absent
from browser storage. The backend must authenticate the peer, authorize session
ownership on every resume, enforce expiry/replay policy, and avoid trusting the
userId input as proof of identity. The reconnect query remains part of the wire
protocol, so it can still enter gateway/proxy access logs. This is a residual
risk, not fixed by the storage change. Redact it in access logs/tracing if sensitive.
Removing it or moving resume credentials to a message/header requires a coordinated
backend protocol change; this demo PR does not invent an unsupported transport.

## A14: cryptographic rendezvous channels

Each connection uses crypto.randomUUID where available, otherwise 16 bytes from
crypto.getRandomValues with UUID v4 version/variant bits. This supports contexts
where randomUUID is unavailable without using Math.random. Missing or failing
cryptographic generation produces a visible error before creating a socket or
requesting the callback. The same channel is encoded into the chat and callback
URLs, and the demo no longer prints the channel or WebSocket URL directly.

Replacing a rendezvous connection closes the old socket and aborts its callback
request. All event handlers and callback continuations check the active socket;
late close, success or failure cannot update the new connection. Sending requires
an OPEN socket and successful callback admission. Abort is best effort: it does
not guarantee a backend has stopped processing an already-received request.

A random channel ID does not authenticate either peer. Production deployment must
authenticate/authorize the frontend WebSocket, backend callback request and backend
WebSocket separately, bind both peers to the intended owner/channel, and enforce
expiry and replay restrictions. Keep public transport on HTTPS/WSS and restrict
callback/backend access. Do not infer these controls from the presence of a random
channel ID or from the demo's free-text userId. Provider callback responses and
infrastructure logs also need appropriate disclosure controls.

## Regression coverage and closure

Run the existing browser suite:

```sh
python3 -B -m unittest discover -s tests -p test_chat_demo_security.py
```

Set BROWSER_BIN if Chrome/Chromium is not on PATH. The sandbox stays enabled by
default; BROWSER_NO_SANDBOX=1 is only for disposable environments that cannot run it.
The suite executes the actual page scripts with mocked WebSocket/fetch. Six browser
runs cover all three demos and the embedded Kubernetes AI page, including a
storage-blocked run for each AI delivery path. A parity test requires the ConfigMap
HTML to match the canonical AI page exactly; the CI paths include the ConfigMap.
The browser cases cover literal rendering,
legacy storage removal, memory reconnect/context isolation, stale socket events,
native/byte channel generation, callback consistency and failure without crypto.
The WebSocket mock models CONNECTING/OPEN/CLOSING/CLOSED and delivers close events
asynchronously. Deferred callback tests cover late success/failure after replacement,
and assertions check disabled controls, preserved drafts and separate stream bubbles.
The suite does not start the Gateway/backend, exercise live authentication or prove a
production channel/session cannot be hijacked.

Deploy the repaired assets, identify the effective gateway/backend admission and
session policies, test authorized/unauthorized resume and peer pairing, and rerun
the partner scan before deployment closure. No backend behavior is changed here.
