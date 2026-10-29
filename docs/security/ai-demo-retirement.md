# AI chat demo retirement

The owner has retired the AI demos that depend on the archived light-genai-4j
backend. [Issue #264](https://github.com/networknt/light-gateway/issues/264) tracks
removal on master and 2.x. This replaces the previously proposed resume-protocol
migration; no new backend protocol is shipped or required by this change.

Removed artifacts:

- config/ai-gateway, including its static page and demo configuration/fixtures.
- config/llmchat-gateway and config/llmchat-rendezvous.
- The embedded Kubernetes chat page, public UI ConfigMap and deployment mount.
- The browser-only regression suite and CI workflow for those deleted demos.

The Kubernetes template remains a generic config-server-bootstrapped gateway,
with no bundled public UI. Historical startup/name defaults are retained for
upgrade compatibility; review explicit identities and config-server values before
deployment.

## Historical security follow-up

A12 text-rendering and A13/A14 browser-state/randomness fixes were previously
merged in PRs #260/#261 and #262/#263. Their historical source evidence remains
available at those revisions. Retirement now removes those example entry points
from this repository; it is not a patch or authorization claim for the archived
backend or for other users of the general WebSocket libraries.

The demo-only browser suite was removed with its subjects. Existing Java gateway
and reusable WebSocket functionality remain outside this removal.

## Deployment cleanup

A source merge does not remove already deployed or cached demos, or ignored local
values files left in an existing checkout. Identify copied
pages, Kubernetes public ConfigMaps, config-server values and demo routes in each
installation. Remove or replace them, clear caches as appropriate, and verify
that public chat/callback endpoints are no longer exposed by those deployments.
The generic template no longer mounts /config/public; any maintained static UI
requires independently supplied assets and explicit routing/mount configuration.

The original Checkmarx A12/A13/A14 results still require artifact/deployment
reconciliation and partner rescan or documented retirement evidence before
closure. No live deployment was modified or qualified by this source removal.
