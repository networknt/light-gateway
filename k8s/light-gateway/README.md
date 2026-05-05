# Light Gateway Kubernetes Template

This folder deploys the Java `light-gateway` as a single-container micro gateway
pod. The gateway uses local `startup.yml` to bootstrap from the config server
and is expected to download the AI gateway values and runtime config for MCP
router and WebSocket router support.

Required deployment values:

- `bootstrapTruststoreBase64`: base64 content of `bootstrap.truststore`
- `lightPortalAuthorization`: bearer token used for config-server access

Common overrides:

- `namespace`
- `name`
- `image.repository`
- `image.tag`
- `startup.host`
- `startup.serviceId`
- `startup.envTag`
- `configServer.uri`

Static web assets:

- The AI gateway `PathResourceHandler` serves files from `path-resource.base`.
- In Kubernetes, `path-resource.base` must be an in-container path, not a workstation path.
- This template mounts the public UI ConfigMap at `/config/public`.
- The matching AI gateway config value is:

```yaml
path-resource.base: /config/public
path-resource.path: /
path-resource.prefix: false
```

If the config server still has a value like `/home/steve/workspace/light-gateway/config/ai-gateway/public`, update that config-server value and reload or redeploy the gateway. The pod cannot see that host filesystem path.



Example local base64 generation:

```sh
base64 -w0 config/ai-gateway/config/bootstrap.truststore
```

The following is the values for testing locally with MicroK8s. 

bootstrapTruststoreBase64: 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

lightPortalAuthorization: eyJhbGciOiJSUzI1NiIsImtpZCI6IkFacDAyTUN1Y3J1WmZGSmJ5eUZ3dWcifQ.eyJpc3MiOiJ1cm46Y29tOm5ldHdvcmtudDpvYXV0aDI6djEiLCJhdWQiOiJ1cm46Y29tLm5ldHdvcmtudCIsImV4cCI6MjA5Mjk1NjM4MywianRpIjoiRnJ6WTdsbllUdzZINGY3eEpPd1MzQSIsImlhdCI6MTc3NzU5NjM4MywibmJmIjoxNzc3NTk2MjYzLCJ2ZXIiOiIxLjAiLCJjaWQiOiIwMTlkZTBmMi1lZTlhLTdjZjAtYWY1OS0wMGY1YzFjZTY0MWYiLCJzY3AiOlsicG9ydGFsLnIiLCJwb3J0YWwudyJdLCJob3N0IjoiMDE5NjRiMDUtNTUyYS03YzRiLTkxODQtNjg1N2U3ZjNkYzVmIiwic2lkIjoiY29tLm5ldHdvcmtudC5haS5nYXRld2F5LTEuMC4wIn0.cvLSRgYlUMQv_-FAhVX2hqHWP_G-q814zYiwTzTUVnErC8oGZsBngnZ9bnGhGe1dZSbqfgHKKFlhz34Z53PC2R8ENvfH45R6fzUDZ_HH8hd_gm336KIiJsAm9F60hRbUSnRHyehD3n0YIIb4OGPnpQvCz-_vglgyPnlIXXauGrNVt4ck3CcQnhYKVHQCr-GE_m5xbJTeu2NWZ_zlRvF0B8EcRHtj1I-psixlH6ayBqR1Lo1AOFaraf6D8FJrMGNek4ByZNP-dEbEF1zRYNY97OeyFxiRtAChBHoxSe-Ba2mtC0deHK7zJ3SsbP98lWWGJwuqdILwdRGxXM0ULmwk7Q


namespace: light-gateway
name: ai-microgateway
image.repository: networknt/light-gateway
image.tag: 2.2.1
startup.host: dev.lightapi.net
startup.serviceId: com.networknt.ai.gateway-1.0.0
startup.envTag: dev
configServer.uri: https://192.168.5.85:8435


• The deployer finds templates from the request’s template object, not from values in the README.

  For an in-container deployer, use a Git URL:

  "template": {
    "repoUrl": "https://github.com/networknt/light-gateway.git",
    "ref": "your-branch",
    "path": "k8s/light-gateway"
  }

  For your current standalone deployer on the host, you can skip Git clone only if it was started with:

  export LIGHT_DEPLOYER_TEMPLATE_BASE_DIR=/home/steve/workspace/light-gateway

  Then template.repoUrl can be any marker like local, and the deployer reads:

  $LIGHT_DEPLOYER_TEMPLATE_BASE_DIR/k8s/light-gateway

  If the deployer is running inside MicroK8s and light-gateway is not mounted into the container, you must commit/push k8s/light-gateway first and use template.repoUrl.

  Example curl for local standalone deployer:

BOOTSTRAP_TRUSTSTORE_BASE64="$(base64 -w0 /home/steve/workspace/light-gateway/config/ai-gateway/config/bootstrap.truststore)"

LIGHT_PORTAL_AUTHORIZATION="Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkFacDAyTUN1Y3J1WmZGSmJ5eUZ3dWcifQ.eyJpc3MiOiJ1cm46Y29tOm5ldHdvcmtudDpvYXV0aDI6djEiLCJhdWQiOiJ1cm46Y29tLm5ldHdvcmtudCIsImV4cCI6MjA5Mjk1NjM4MywianRpIjoiRnJ6WTdsbllUdzZINGY3eEpPd1MzQSIsImlhdCI6MTc3NzU5NjM4MywibmJmIjoxNzc3NTk2MjYzLCJ2ZXIiOiIxLjAiLCJjaWQiOiIwMTlkZTBmMi1lZTlhLTdjZjAtYWY1OS0wMGY1YzFjZTY0MWYiLCJzY3AiOlsicG9ydGFsLnIiLCJwb3J0YWwudyJdLCJob3N0IjoiMDE5NjRiMDUtNTUyYS03YzRiLTkxODQtNjg1N2U3ZjNkYzVmIiwic2lkIjoiY29tLm5ldHdvcmtudC5haS5nYXRld2F5LTEuMC4wIn0.cvLSRgYlUMQv_-FAhVX2hqHWP_G-q814zYiwTzTUVnErC8oGZsBngnZ9bnGhGe1dZSbqfgHKKFlhz34Z53PC2R8ENvfH45R6fzUDZ_HH8hd_gm336KIiJsAm9F60hRbUSnRHyehD3n0YIIb4OGPnpQvCz-_vglgyPnlIXXauGrNVt4ck3CcQnhYKVHQCr-GE_m5xbJTeu2NWZ_zlRvF0B8EcRHtj1I-psixlH6ayBqR1Lo1AOFaraf6D8FJrMGNek4ByZNP-dEbEF1zRYNY97OeyFxiRtAChBHoxSe-Ba2mtC0deHK7zJ3SsbP98lWWGJwuqdILwdRGxXM0ULmwk7Q"


Here is the command to create the namespace first. 

```
kubectl create namespace light-gateway --dry-run=client -o yaml | kubectl apply -f -
```

Here is the curl command to deploy and it is working.

```
 curl -sS http://127.0.0.1:8437/deployments \
    -H 'content-type: application/json' \
    -d "$(jq -n \
      --arg bootstrap "$BOOTSTRAP_TRUSTSTORE_BASE64" \
      --arg auth "$LIGHT_PORTAL_AUTHORIZATION" \
      '{
        hostId: "01964b05-552a-7c4b-9184-6857e7f3dc5f",
        instanceId: "ai-microgateway-dev",
        environment: "dev",
        clusterId: "local",
        namespace: "light-gateway",
        action: "deploy",
        values: {
          namespace: "light-gateway",
          name: "ai-microgateway",
          image: { repository: "networknt/light-gateway", tag: "2.2.1", pullPolicy: "IfNotPresent" },
          startup: { host: "dev.lightapi.net", serviceId: "com.networknt.ai.gateway-1.0.0", envTag: "dev" },
          configServer: { uri: "https://192.168.5.85:8435", verifyHostName: false },
          lightEnv: "dev",
          light4jConfigPassword: "dev",
          configServerTruststorePassword: "password",
          lightPortalAuthorization: $auth,
          bootstrapTruststoreBase64: $bootstrap
        },
        template: { repoUrl: "local", ref: "main", path: "k8s/light-gateway" }
      }')"
```

This is the old command. 

```
curl --location --request POST 'http://127.0.0.1:8437/deployments' \
--header 'Content-Type: application/json' \
--data-raw '{
  "hostId": "01964b05-552a-7c4b-9184-6857e7f3dc5f",
  "instanceId": "ai-microgateway-dev",
  "environment": "dev",
  "clusterId": "local",
  "namespace": "light-gateway",
  "action": "deploy",
  "values": {
    "namespace": "light-gateway",
    "name": "ai-microgateway",
    "image": {
      "repository": "networknt/light-gateway",
      "tag": "2.2.1",
      "pullPolicy": "IfNotPresent"
    },
    "startup": {
      "host": "dev.lightapi.net",
      "serviceId": "com.networknt.ai.gateway-1.0.0",
      "envTag": "dev"
    },
    "configServer": {
      "uri": "https://192.168.5.85:8435",
      "verifyHostName": false
    },
    "lightEnv": "dev",
    "light4jConfigPassword": "DEV",
    "configServerTruststorePassword": "password",
    "lightPortalAuthorization": "$LIGHT_PORTAL_AUTHORIZATION",
    "bootstrapTruststoreBase64": "$BOOTSTRAP_TRUSTSTORE_BASE64"
  },
  "template": {
    "repoUrl": "local",
    "ref": "master",
    "path": "k8s/light-gateway"
  },
  "options": {
    "waitForRollout": true,
    "timeoutSeconds": 300
  }
}'
```
Response

```
{"requestId":"019de170-f576-7410-9d91-81c2f1ecf459","action":"deploy","status":"accepted","deployerId":"local-light-deployer","clusterId":"local","namespace":"light-gateway","resources":[],"events":[]}
```


To connect to the microK8s for real deployment. 


cd /home/steve/workspace/light-fabric/apps/light-deployer


```
KUBECONFIG=/var/snap/microk8s/current/credentials/client.config \
LIGHT_DEPLOYER_KUBE_MODE=real \
LIGHT_DEPLOYER_TEMPLATE_BASE_DIR=/home/steve/workspace/light-gateway \
./run.sh
```

Then check the existing request history:

```
curl -sS http://127.0.0.1:8437/deployments \
    -H 'content-type: application/json' \
    -d '{
      "requestId": "019df12b-0b4f-7f83-aa8a-473f8f6b90d3",
      "hostId": "01964b05-552a-7c4b-9184-6857e7f3dc5f",
      "instanceId": "ai-microgateway",
      "environment": "dev",
      "clusterId": "local",
      "namespace": "light-gateway",
      "action": "status",
      "template": {
        "repoUrl": "local",
        "ref": "main",
        "path": "k8s/light-gateway"
      }
    }' | jq .
```

For the next deploy, you can also open the live event stream first:

```
curl -N "http://127.0.0.1:8437/events?requestId=019de181-d5b8-70c2-b626-c5942b15b3b5"
```

After deploying with LIGHT_DEPLOYER_KUBE_MODE=real, verify MicroK8s directly:

```
microk8s kubectl -n light-gateway get all
microk8s kubectl -n light-gateway get events --sort-by=.metadata.creationTimestamp
```


  For in-cluster/container deployer, change only template after pushing the templates:

  "template": {
    "repoUrl": "https://github.com/networknt/light-gateway.git",
    "ref": "your-branch",
    "path": "k8s/light-gateway"
  }

  Also: avoid committing the real lightPortalAuthorization value in README. Keep it as an env var or deployment secret input.


To check the deployment. 

```
kubectl -n light-gateway get pods
kubectl -n light-gateway logs deploy/ai-microgateway
```

To access the static UI from a browser when the Service is `ClusterIP`, port-forward the gateway service:

```sh
kubectl -n light-gateway port-forward svc/ai-microgateway 8443:8443
```

Then open:

```text
https://localhost:8443/
```

The page connects back to the same host with `wss://localhost:8443/chat`. For shared access without port-forwarding, expose the service through an Ingress or change the Service to `NodePort`/`LoadBalancer` according to the target cluster.

To clean up and redeploy. 

```
kubectl -n light-gateway delete deploy,svc,cm,secret \
-l app.kubernetes.io/managed-by=light-deployer
```

Access pod shell. 

```
kubectl exec -it ai-microgateway-d7b864586-f9kgr -n light-gateway -- /bin/sh
```
