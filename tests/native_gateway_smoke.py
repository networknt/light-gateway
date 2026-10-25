#!/usr/bin/env python3
"""Run an isolated health-only gateway fixture; never use deployment configuration."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--binary", type=Path)
    target.add_argument("--jar", type=Path)
    args = parser.parse_args()
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="gateway-native-smoke-") as directory:
        config = Path(directory)
        (config / "server.yml").write_text(f"""ip: 127.0.0.1
httpPort: {port}
enableHttp: true
enableHttps: false
enableHttp2: false
enableRegistry: false
ioThreads: 1
workerThreads: 2
serviceId: native-gateway-smoke
shutdownTimeout: 1000
""")
        (config / "handler.yml").write_text("""enabled: true
handlers:
  - com.networknt.health.HealthGetHandler@health
chains: {}
paths:
  - path: /health
    method: get
    exec: [health]
defaultHandlers: [health]
""")
        (config / "health.yml").write_text("enabled: true\nuseJson: true\ndownstreamEnabled: false\n")
        (config / "service.yml").write_text("singletons: []\n")
        (config / "values.yml").write_text("{}\n")
        (config / "logback.xml").write_text("""<configuration>
  <appender name="console" class="ch.qos.logback.core.ConsoleAppender">
    <encoder><pattern>%level %logger %msg%n</pattern></encoder>
  </appender>
  <root level="WARN"><appender-ref ref="console"/></root>
</configuration>
""")
        options = [f"-Dlight-4j-config-dir={config}", f"-Dlogback.configurationFile={config / 'logback.xml'}"]
        command = [str(args.binary.resolve()), *options] if args.binary else ["java", *options, "-jar", str(args.jar.resolve())]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with (config / "gateway.log").open("w+") as log:
            process = subprocess.Popen(command, cwd=config, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline and process.poll() is None:
                    try:
                        with opener.open(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                            payload = response.read()
                            assert response.status == 200
                            assert response.headers.get_content_type() == "application/json"
                            assert json.loads(payload) == {"result": "OK"}, payload
                            print("Gateway health-only smoke passed: HTTP 200, Jackson JSON response and native metadata")
                            return
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                raise AssertionError("Gateway fixture did not become ready")
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


if __name__ == "__main__":
    main()
