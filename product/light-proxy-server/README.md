The light proxy server configures the light gateway to bring a  legacy API to the light ecosystem with all the cross-cutting concerns addressed on the same host.

### LPS configuration

For incoming requests, the light proxy server will execute a chain of middleware handlers before transferring the request to the backend API.

When the backend API calls another API, it calls the localhost light-proxy-server with a header of serviceId or service_id or service_url. This is the default configuration. You can also change the following properties in values.yml to all the light-proxy-server to differentiate ingress or egress traffic based on the protocol. 

```
# sidecar.yml

sidecar.egressIngressIndicator: protocol
```

For incoming ingress requests from outside, use HTTPS; for outgoing egress requests from the backend API, use HTTP as it is localhost. So the LPC server starts with both HTTP 8080 and HTTPS 8443 ports. 

We will use the default configuration header for the current demo configuration to indicate if the traffic is ingress or egress. As two ports are used, we can also use the protocol to differentiate the traffic. 

The demo API is the market API, which will subsequently call the petstore API. 

### Audience Validation

We use this config folder for the JWT audience validation test for the following three scenarios:

1. Single OAuth 2.0 provider

This is the default configuration for the light-proxy-server. The light proxy server will validate the audience against the audience in the JWT token. If the audience is not matched, the request will be rejected.

The values.yml file has a backup with the same content as the values-single.yml file. 

2. Multiple OAuth 2.0 providers

3. Unified Security


