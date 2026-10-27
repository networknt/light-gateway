#!/usr/bin/env python3
"""Qualify gateway TLS with temporary local CAs and loopback-only upstreams."""
import argparse
from contextlib import ExitStack
import hashlib
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid

from native_gateway_smoke import Upstream, request, write_config


def tool(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if result.returncode:
        raise RuntimeError(f"Fixture tool failed: {command[0]}\n{result.stderr.decode(errors='replace')}")
    return result.stdout


def certificates(config, base_store):
    for name in ("custom", "default", "untrusted"):
        tool(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "2",
              "-subj", f"/CN=Gateway fixture {name} CA", "-addext", "basicConstraints=critical,CA:TRUE",
              "-addext", "keyUsage=critical,keyCertSign,cRLSign", "-addext", "subjectKeyIdentifier=hash",
              "-keyout", str(config / f"{name}-ca.key"), "-out", str(config / f"{name}-ca.pem")])
        tool(["openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes", "-sha256",
              "-subj", "/CN=localhost", "-keyout", str(config / f"{name}.key"),
              "-out", str(config / f"{name}.csr")])
        extensions = config / f"{name}.ext"
        extensions.write_text("subjectAltName=DNS:localhost\nbasicConstraints=critical,CA:FALSE\n"
                              "keyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n"
                              "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n")
        tool(["openssl", "x509", "-req", "-sha256", "-days", "2", "-in", str(config / f"{name}.csr"),
              "-CA", str(config / f"{name}-ca.pem"), "-CAkey", str(config / f"{name}-ca.key"),
              "-CAcreateserial", "-extfile", str(extensions), "-out", str(config / f"{name}.pem")])
    tool(["openssl", "pkcs12", "-export", "-name", "fixture", "-inkey", str(config / "custom.key"),
          "-in", str(config / "custom.pem"), "-certfile", str(config / "custom-ca.pem"),
          "-out", str(config / "server.p12"), "-passout", "pass:password"])
    (config / "default.truststore").write_bytes(base_store)
    for name, store, password in (("custom", "client.truststore", "password"),
                                  ("default", "default.truststore", "changeit")):
        tool(["keytool", "-importcert", "-noprompt", "-alias", f"gateway-fixture-{name}",
              "-file", str(config / f"{name}-ca.pem"), "-keystore", str(config / store),
              "-storetype", "JKS", "-storepass", password])


def upstream(stack, config, name):
    class CountingUpstream(Upstream):
        calls = []

    server = stack.enter_context(ThreadingHTTPServer(("127.0.0.1", 0), CountingUpstream))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config / f"{name}.pem", config / f"{name}.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stack.callback(thread.join, 5)
    stack.callback(server.shutdown)
    return server.server_port, CountingUpstream.calls


def configure(config, port, ports):
    write_config(config, port, ports["custom"])
    (config / "server.yml").write_text(f"""ip: 127.0.0.1
httpsPort: {port}
enableHttp: false
enableHttps: true
enableHttp2: false
enableRegistry: false
enableTwoWayTls: false
keystoreName: server.p12
keystorePass: password
keyPass: password
ioThreads: 1
workerThreads: 4
serviceId: native-gateway-tls-smoke
shutdownTimeout: 1000
""")
    (config / "values.yml").write_text("""client.verifyHostname: true
client.loadDefaultTrustStore: true
client.loadTrustStore: true
client.trustStore: client.truststore
client.trustStorePass: password
client.loadKeyStore: false
client.defaultCertPassword: changeit
client.tlsVersion: TLSv1.2
""")
    routes = [(name, f"https://localhost:{ports[name]}") for name in ports]
    routes.append(("hostname", f"https://127.0.0.1:{ports['custom']}"))
    (config / "external-service.yml").write_text("""enabled: true
connectTimeout: 1000
timeout: 3000
maxConnectionRetries: 1
enableHttp2: false
metricsInjection: false
pathPrefixes:
""" + "".join(f"  - pathPrefix: /native/{name}\n    host: {url}\n" for name, url in routes))
    paths = "".join(f"""  /native/{name}:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema: {{type: object}}
      responses:
        '200': {{description: Forwarded TLS fixture}}
""" for name, _ in routes)
    (config / "openapi.yml").write_text("openapi: 3.0.3\ninfo: {title: TLS fixture, version: '1'}\n"
                                        "servers: [{url: /}]\npaths:\n" + paths)


def command(args, config, container_name):
    if args.image:
        invocation = ["docker", "run", "--rm", "--pull=never", "--name", container_name,
                "--network=host", "--user", f"{os.getuid()}:{os.getgid()}",
                "-v", f"{config}:/config:ro"]
        if not args.stock_store:
            invocation += ["-v", f"{config / 'default.truststore'}:/app/cacerts:ro"]
        return [*invocation, args.image]
    options = [f"-Dlight-4j-config-dir={config}", f"-Dlogback.configurationFile={config / 'logback.xml'}",
               f"-Djavax.net.ssl.trustStore={config / 'default.truststore'}",
               "-Djavax.net.ssl.trustStoreType=JKS", "-Djavax.net.ssl.trustStorePassword=changeit"]
    if args.binary:
        return [str(args.binary.resolve()), *options]
    return ["java", *options, "-jar", str(args.jar.resolve())]


def rejected(opener, url):
    try:
        request(opener, url)
    except urllib.error.URLError as error:
        assert isinstance(error.reason, ssl.SSLCertVerificationError), error
        return {"verify_code": error.reason.verify_code, "verify_message": error.reason.verify_message}
    else:
        raise AssertionError("Invalid listener certificate was accepted")


def exercise(port, config, calls, stock_store=False):
    outcomes = {}
    context = ssl.create_default_context(cafile=str(config / "custom-ca.pem"))
    context.verify_flags |= ssl.VERIFY_X509_STRICT
    context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context))
    base = f"https://localhost:{port}"
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        try:
            assert request(opener, base + "/health") == (200, "application/json", {"result": "OK"})
            break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    else:
        raise AssertionError("TLS gateway did not become ready")
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        with context.wrap_socket(connection, server_hostname="localhost") as secured:
            assert secured.version() == "TLSv1.2", secured.version()
            outcomes["listener_tls"] = {"version": secured.version(), "cipher": secured.cipher()}
    outcomes["listener_hostname_rejection"] = rejected(opener, f"https://127.0.0.1:{port}/health")
    wrong_ca = ssl.create_default_context(cafile=str(config / "untrusted-ca.pem"))
    outcomes["listener_ca_rejection"] = rejected(urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                       urllib.request.HTTPSHandler(context=wrong_ca)), base + "/health")
    value = {"name": "tls", "amount": 7}
    for name in ("custom", "default"):
        response = request(opener, base + f"/native/{name}", value)
        outcomes[f"{name}_forwarding"] = response
        if name == "default" and stock_store:
            assert response[0] == 400 and response[2]["code"] == "ERR10011", response
        else:
            assert response == (200, "application/json", {"forwarded": value}), (name, response)
    assert [len(calls[name]) for name in ("custom", "default", "untrusted")] == [1, 0 if stock_store else 1, 0], calls
    for name in ("untrusted", "hostname"):
        status, media, body = request(opener, base + f"/native/{name}", value)
        outcomes[f"{name}_rejection"] = {"status": status, "media": media, "code": body["code"]}
        # Existing ExceptionHandler maps failed TLS handshakes to this structured response.
        assert (status, media, body["code"]) == (400, "application/json", "ERR10011"), (name, status, body)
    assert [len(calls[name]) for name in ("custom", "default", "untrusted")] == [1, 0 if stock_store else 1, 0], "Rejected TLS reached an upstream"
    outcomes["warm_recovery"] = request(opener, base + "/native/custom", value)
    assert outcomes["warm_recovery"] == (200, "application/json", {"forwarded": value})
    assert len(calls["custom"]) == 2, calls
    outcomes["upstream_calls"] = {name: len(value) for name, value in calls.items()}
    assert set(outcomes) == {"listener_tls", "listener_hostname_rejection", "listener_ca_rejection",
                             "custom_forwarding", "default_forwarding", "untrusted_rejection",
                             "hostname_rejection", "warm_recovery", "upstream_calls"}
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--binary", type=Path)
    target.add_argument("--jar", type=Path)
    target.add_argument("--image")
    parser.add_argument("--stock-store", action="store_true", help="Exercise the unmodified image truststore")
    args = parser.parse_args()
    if args.stock_store and not args.image:
        parser.error("--stock-store requires --image")
    if args.image and os.getuid() == 0:
        parser.error("Image qualification requires a non-root caller for explicit --user")
    mode = "alpine" if args.image else "native" if args.binary else "jvm"
    if args.stock_store:
        mode += "-stock-store"
    evidence = Path(__file__).resolve().parents[1] / "target" / "native-tls"
    evidence.mkdir(parents=True, exist_ok=True)
    result_path = evidence / f"{mode}.json"
    result_path.write_text(json.dumps({"schema": 1, "mode": mode, "passed": False}) + "\n")
    artifact = {}
    if args.image:
        base_store = tool(["docker", "run", "--rm", "--pull=never", "--network=none", "--entrypoint", "cat", args.image, "/app/cacerts"])
        artifact["image_id"] = tool(["docker", "image", "inspect", "--format", "{{.Id}}", args.image]).decode().strip()
        artifact["alpine_release"] = tool(["docker", "run", "--rm", "--pull=never", "--network=none", "--entrypoint", "cat", args.image, "/etc/alpine-release"]).decode().strip()
        artifact["sha256"] = tool(["docker", "run", "--rm", "--pull=never", "--network=none", "--entrypoint", "sha256sum", args.image, "/app/server"]).decode().split()[0]
    else:
        base_store = (Path(shutil.which("keytool")).resolve().parents[1] / "lib/security/cacerts").read_bytes()
        artifact["sha256"] = hashlib.sha256((args.binary or args.jar).read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="gateway-native-tls-") as directory, ExitStack() as stack:
        config = Path(directory)
        certificates(config, base_store)
        ports, calls = {}, {}
        for name in ("custom", "default", "untrusted"):
            ports[name], calls[name] = upstream(stack, config, name)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        configure(config, port, ports)
        container_name = f"gateway-tls-{uuid.uuid4().hex}"
        with (evidence / f"{mode}.log").open("w+") as log:
            process = subprocess.Popen(command(args, config, container_name), cwd=config, stdout=log, stderr=subprocess.STDOUT)
            try:
                outcomes = exercise(port, config, calls, args.stock_store)
                if args.image:
                    artifact["runtime_uid"] = int(tool(["docker", "exec", container_name, "id", "-u"]))
                    assert artifact["runtime_uid"] != 0
            except Exception as error:
                log.flush()
                log.seek(0)
                raise AssertionError(f"{mode} TLS smoke failed: {error}\n{log.read()[-12000:]}") from error
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if args.image:
                    cleanup = subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=10)
                    if cleanup.returncode and b"No such container" not in cleanup.stderr:
                        raise RuntimeError(f"Unable to remove fixture container {container_name}: {cleanup.stderr!r}")
        result_path.write_text(json.dumps({
            "schema": 1, "mode": mode, "passed": True, "artifact": artifact,
            "default_truststore_sha256": hashlib.sha256(base_store).hexdigest(),
            "selected_default_truststore_file_sha256": hashlib.sha256(base_store if args.stock_store else
                                                                  (config / "default.truststore").read_bytes()).hexdigest(),
            "store_mode": "bundled-unmodified" if args.stock_store else "fixture-augmented",
            "measurements": outcomes,
        }, indent=2) + "\n")
    print(f"Gateway TLS smoke passed ({mode}): measured HTTPS, forwarding, rejection and recovery cases")


if __name__ == "__main__":
    main()
