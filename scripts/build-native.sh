#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
# The source-build workflow must qualify this JAR first; do not resolve snapshots in Docker.
test -s target/light-gateway.jar || { echo "Build the source-qualified shaded JAR first" >&2; exit 1; }
mkdir -p target/native
docker run --rm --pull="${GRAALVM_PULL:-never}" --network=none --user "$(id -u):$(id -g)" \
    -v "$PWD:/workspace" -w /workspace --entrypoint native-image \
    "${GRAALVM_IMAGE:-ghcr.io/graalvm/native-image-community:25@sha256:0d936f32bb8acb5bc60c41b33e05f064d7a6aaf36b726538296c54949bd4a3c0}" \
    @/workspace/docker/native-image.args -o /workspace/target/native/server \
    -cp /workspace/target/light-gateway.jar com.networknt.server.Server
test -x target/native/server
