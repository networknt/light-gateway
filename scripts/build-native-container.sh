#!/usr/bin/env bash
# Build from a clean gateway checkout using an already source-installed prerequisite cache.
set -euo pipefail
if [[ $# != 3 ]]; then
    echo "Usage: $0 ISOLATED_MAVEN_REPO LIGHT_4J_SOURCE IMAGE_TAG" >&2
    echo "Install migrated prerequisites from source first; see README: Native container build." >&2
    exit 2
fi
repository=$(cd -- "$1" && pwd -P)
core=$(cd -- "$2" && pwd -P)
tag=$3
[[ "$repository" != "$HOME/.m2/repository" ]] || { echo 'Use an isolated source cache, not ~/.m2.' >&2; exit 2; }
[[ -f "$core/scripts/jackson3_artifact_audit.py" ]] || { echo 'Missing source-audit tooling in LIGHT_4J_SOURCE.' >&2; exit 2; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mvn -o "-Dmaven.repo.local=$repository" clean install
mvn -o -B -Dstyle.color=never "-Dmaven.repo.local=$repository" dependency:tree > target/native-container-dependencies.txt
python3 "$core/scripts/jackson3_artifact_audit.py" --repository "$repository" \
    --tree target/native-container-dependencies.txt --report target/native-container-artifact-audit.json --require-jackson3-only
docker build -f docker/Dockerfile-Native -t "$tag" .
