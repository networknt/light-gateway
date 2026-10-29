# Light Gateway Kubernetes Template

This template deploys Java light-gateway as a single-container micro gateway.
Local startup.yml bootstraps runtime configuration from the config server.
Choose the maintained configuration for the service being deployed; this template
no longer downloads or serves an AI chat demo by default.

## Required deployment values

- bootstrapTruststoreBase64: base64 content of your config-server truststore.
- lightPortalAuthorization: a short-lived config-server access token supplied at runtime.
- startup.host, startup.serviceId and startup.envTag: your configuration identity.
- configServer.uri: the intended config-server endpoint.

Common overrides include namespace, name, image.repository, image.tag, resource
requests/limits and config-server TLS settings. Use render-request.json as a
structural example and replace its environment-specific values before use.
Do not commit runtime tokens or secret values.

The deployment mounts a writable /config workspace, startup.yml, and the supplied
bootstrap truststore. It sets STATUS_HOST_IP to ${name}.${namespace} so service
registration uses the Kubernetes Service DNS name rather than a pod IP.

## Render or deploy

Use k8s/light-gateway as the deployer template path. For a Git-backed template:

```json
{
  "template": {
    "repoUrl": "https://github.com/networknt/light-gateway.git",
    "ref": "your-reviewed-ref",
    "path": "k8s/light-gateway"
  }
}
```

For a local deployer, set LIGHT_DEPLOYER_TEMPLATE_BASE_DIR to this checkout and
use the same template path. For an in-cluster deployer, use a pushed Git revision
or explicitly mount that checkout. Supply the actual truststore and access token
through the deployer's supported runtime values/secret inputs.

## AI demo retirement

The embedded chat page and its public ConfigMap/volume mount have been removed.
No public UI is served by this template. Applications that need static resources
must supply their own assets, mounts and matching PathResourceHandler settings;
path-resource.base must refer to a path inside the container.

Existing clusters are not changed by a source merge. Remove the old public UI
ConfigMap, cached pages and demo-specific handler/router configuration from the
actual deployment. Review startup.serviceId overrides that still select the
retired AI configuration. See the [retirement guide](../../docs/security/ai-demo-retirement.md).

Health checks, config-server bootstrap and the gateway Service remain available.
Cluster ingress, TLS/HSTS and admission policy must be configured for the target
deployment and are not qualified by rendering these templates.

## Upgrade identity compatibility

This retirement preserves the historical default startup.serviceId
(com.networknt.ai.gateway-1.0.0) and the sample name/instanceId in render-request.json.
The legacy names do not enable the removed demo, but they may still select old
config-server values. Review those values before deployment. Keep an existing
name, instanceId and service identity when updating that deployment; changing them
is a separate migration that can create new Kubernetes resources or change service
registration/configuration lookup. New deployments should supply their intended
identity explicitly rather than infer it from this sample.

The retired local config/ai-gateway/config/values.yml path remains ignored because
an existing checkout may still contain a credential-bearing local file. Git pull
will not erase it; handle local cleanup without staging or publishing its values.
