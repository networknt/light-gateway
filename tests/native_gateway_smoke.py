#!/usr/bin/env python3
"""Exercise real gateway validation, body, forwarding and service paths on loopback."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request


class Upstream(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        value = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.calls.append(value)
        body = json.dumps({"forwarded": value}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def write_config(config, port, upstream):
    files = {
        "server.yml": f"""ip: 127.0.0.1
httpPort: {port}
enableHttp: true
enableHttps: false
enableHttp2: false
enableRegistry: false
ioThreads: 1
workerThreads: 4
serviceId: native-gateway-smoke
shutdownTimeout: 1000
""",
        "handler.yml": """enabled: true
handlers:
  - com.networknt.health.HealthGetHandler@health
  - com.networknt.exception.ExceptionHandler@exception
  - com.networknt.body.BodyHandler@body
  - com.networknt.openapi.OpenApiHandler@openapi
  - com.networknt.openapi.ValidatorHandler@validator
  - com.networknt.proxy.ExternalServiceHandler@external
  - com.networknt.cache.CacheExplorerHandler@cache
chains: {}
paths:
  - path: /health
    method: get
    exec: [health]
  - path: /native-cache
    method: get
    exec: [exception, cache]
  - path: /native/*
    method: post
    exec: [exception, body, openapi, validator, external]
defaultHandlers: [health]
""",
        "health.yml": "enabled: true\nuseJson: true\ndownstreamEnabled: false\n",
        "body.yml": "enabled: true\ncacheRequestBody: true\n",
        "openapi-handler.yml": "multipleSpec: false\nignoreInvalidPath: false\n",
        "openapi-validator.yml": "enabled: true\nvalidateResponse: false\n",
        "external-service.yml": f"""enabled: true
connectTimeout: 1000
timeout: 3000
maxConnectionRetries: 1
enableHttp2: false
metricsInjection: false
pathPrefixes:
  - pathPrefix: /native/
    host: http://127.0.0.1:{upstream}
""",
        "openapi.yml": """openapi: 3.0.3
info: {title: Native gateway validation fixture, version: '1.0'}
servers: [{url: /}]
paths:
  /native/echo:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, amount]
              properties:
                name: {type: string, minLength: 1}
                amount: {type: integer, minimum: 1}
      responses:
        '200': {description: Forwarded fixture response}
""",
        "service.yml": """singletons:
  - com.networknt.cache.CacheManager:
      - com.networknt.cache.CaffeineCacheManager
""",
        # HTTP-only fixture: default truststore loading and native TLS are not qualified here.
        "values.yml": "client.loadDefaultTrustStore: false\n",
        "logback.xml": """<configuration>
  <appender name="console" class="ch.qos.logback.core.ConsoleAppender">
    <encoder><pattern>%level %logger %msg%n</pattern></encoder>
  </appender>
  <root level="WARN"><appender-ref ref="console"/></root>
</configuration>
""",
    }
    for name, contents in files.items():
        (config / name).write_text(contents)


def request(opener, url, value=None):
    data = None if value is None else json.dumps(value).encode()
    query = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        response = opener.open(query, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers.get_content_type(), json.loads(response.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--binary", type=Path)
    target.add_argument("--jar", type=Path)
    parser.add_argument("--java-option", action="append", default=[])
    args = parser.parse_args()
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    with ThreadingHTTPServer(("127.0.0.1", 0), Upstream) as upstream:
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix="gateway-native-smoke-") as directory:
                config = Path(directory)
                write_config(config, port, upstream.server_port)
                options = [f"-Dlight-4j-config-dir={config}", f"-Dlogback.configurationFile={config / 'logback.xml'}"]
                command = [str(args.binary.resolve()), *options] if args.binary else ["java", *args.java_option, *options, "-jar", str(args.jar.resolve())]
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with (config / "gateway.log").open("w+") as log:
                    process = subprocess.Popen(command, cwd=config, stdout=log, stderr=subprocess.STDOUT)
                    try:
                        deadline = time.monotonic() + 40
                        while time.monotonic() < deadline and process.poll() is None:
                            try:
                                assert request(opener, f"http://127.0.0.1:{port}/health") == (200, "application/json", {"result": "OK"})
                                break
                            except (urllib.error.URLError, TimeoutError):
                                time.sleep(0.1)
                        else:
                            raise AssertionError("Gateway fixture did not become ready")
                        base = f"http://127.0.0.1:{port}"
                        # Cache manager is constructed through the real nonempty service mapping.
                        assert request(opener, base + "/native-cache?name=fixture") == (200, "application/json", None)
                        valid = {"name": "native", "amount": 7}
                        assert request(opener, base + "/native/echo", valid) == (200, "application/json", {"forwarded": valid})
                        before = len(Upstream.calls)
                        for invalid in ({"name": "native"}, {"name": "", "amount": 0}, {"name": 7, "amount": "bad"}):
                            status, media_type, body = request(opener, base + "/native/echo", invalid)
                            assert status == 400 and media_type == "application/json", (status, media_type, body)
                            assert body["code"].startswith("ERR"), body
                        assert len(Upstream.calls) == before == 1, "invalid requests reached upstream"
                        print("Gateway smoke passed: real service/handler construction, JSON body, OpenAPI/JSON Schema validation, forwarding and structured errors")
                    except Exception:
                        log.seek(0)
                        diagnostic = log.read()
                        Path(__file__).resolve().parents[1].joinpath("target/native-smoke-failure.log").write_text(diagnostic)
                        raise AssertionError("Gateway smoke failed:\n" + diagnostic[-12000:])
                    finally:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
        finally:
            upstream.shutdown()
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
