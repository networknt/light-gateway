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


### Tutorial

There are three values.yml configurations in the product/light-proxy-server folder based on single, multiple and unified security models. There are three values.yml configurations in the product/light-proxy-server folder based on single, multiple and unified security models. You can copy the corresponding values-xxx.yml to values.yml for your configuration and start the server from the folder based on your requirement.

The demo relies on two APIs: Petstore and Market.

Check out light-example-4j from GitHub and start both APIs on the command line.

```
cd ~/networknt/light-example-4j/rest/market
mvn clean install -Prelease
java -jar target/server.jar
```

On another terminal.

```
cd ~/networknt/light-example-4j/rest/petstore-maven-single
mvn clean install -Prelease
java -jar target/server.jar

```

Once all three servers are up and running, you can send the following command.

```
curl --location 'https://localhost:8443/abc/products' \
--header 'Authorization: Bearer eyJraWQiOiJabHFic'
```

Please replace the token from your OAuth 2.0 provider in the above curl command.

This request will reach the LPS, and LPS will proxy it to the market API. Once the market API receives the request, it will call the LPS again to access the petstore API. Before the LPS route the request to the petstore API, it will go to the OAuth 2.0 provider to get a client credentials token based on the configuration.
