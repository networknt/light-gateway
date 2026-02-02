import requests
import sseclient
import json
import threading
import time
import uuid

# Configuration
BASE_URL = "https://localhost:8443"
MCP_PATH = "/mcp"
VERIFY_SSL = False  # Set to True if you have valid certs

def sse_listener(url):
    print(f"Connecting to SSE at {url}...")
    try:
        response = requests.get(url, stream=True, verify=VERIFY_SSL)
        client = sseclient.SSEClient(response)
        for event in client.events():
            print(f"\n[SSE] Received event: {event.event}")
            print(f"[SSE] Data: {event.data}")
            if event.event == 'endpoint':
                print(f"[SSE] Endpoint received: {event.data}")
    except Exception as e:
        print(f"[SSE] Error: {e}")

def run_tests():
    # Start SSE listener in background
    sse_url = f"{BASE_URL}{MCP_PATH}"
    t = threading.Thread(target=sse_listener, args=(sse_url,))
    t.daemon = True
    t.start()

    time.sleep(1) # Wait for connection

    print("\n[Client] Sending 'initialize' request...")
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        },
        "id": 1
    }

    # We can send to /mcp directly. The handler extracts sessionId from query if needed,
    # but for now we just use the base path as the handler supports POST /mcp.
    # Note: If you extracted sessionId from SSE 'endpoint' event, you should append it: /mcp?sessionId=...
    # For this test, we assume the server handles stateless POST or we haven't parsed the ID yet.

    post_url = f"{BASE_URL}{MCP_PATH}"
    try:
        res = requests.post(post_url, json=init_payload, verify=VERIFY_SSL)
        print(f"[Client] Response ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"[Client] POST Error: {e}")

    time.sleep(1)

    print("\n[Client] Sending 'tools/list' request...")
    list_payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    try:
        res = requests.post(post_url, json=list_payload, verify=VERIFY_SSL)
        print(f"[Client] Response ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"[Client] POST Error: {e}")

    time.sleep(1)

if __name__ == "__main__":
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    run_tests()
    time.sleep(5) # Keep alive to see SSE
