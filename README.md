## light-gateway:   

A standalone gateway combined both light-router and light-proxy


  
    light-gateway can be deployed as API gateway to handle restful request/response related functionalities which include:
     
     - Package and deployed as separate module to handle Cross-Cutting Concerns for main container/service in the same pod. In this case, the main service only need care about the http request/response and business logic
     
     - Ingress traffic: client  request(legacy) will come to light-gateway first, light-gateway act as a proxy to delegate light client features, which include, openapi schema validation, observability, monitoring, logging, JWT verify, etc. Then forward the request to main service.
      
     - Egress traffic: main service call through light-gateway for egress traffic; in this case, light-gateway act as a router to delegate light client features, which include service discovery, SSL handshake, JWT token management, etc. Then forward the request to server API.




### Architecture diagram



- Se light-gateway deployment :

![Ligh-Mesh Architecture](docs/mesh-2.png)

By default, the light-gateway works as internet gateway for both proxy/router features. Most of middleware handlers are commented out. User can enable it  based on different user cases.

Please refer to default setting for detail:

 [handler](https://github.com/networknt/light-gateway/blob/master/src/main/resources/config/handler.yml)  
 [values](https://github.com/networknt/light-gateway/blob/master/src/main/resources/config/values.yml)  

### Light-gateway features and config setting:

- Proxy 

  Light-gateway Proxy used for dispatch the request from light-4j API to existing system (legacy). Since existing system may not have some microservice features, for example:
  
  - Audit log
  - JWT verify
  - Metrics  
  - Openapi schema validation
  
  Light-gateway proxy can handle those features and forward the request to  existing system.
      
  The major config for proxy is "proxy.host", user can define a list of proxy destination host separate by ",'. For example
  
  proxy.host: https://localhost:9443,http://localhost:8080,https://www.networknt.com

- Router

  Light-gateway Router used for dispatch the request from existing system to light-4j restful API. Normally the existing system doesn't support some microservice feature for service call:
   
  - Service discovery 
  - Audit log
  - JWT populate
  - Metrics

  Light-gateway Router can handle those features and forward the request to new microservice API.
  
  Light-gateway Router be triggered if the request header include key "service_id" or "service_url" (if both existing, service_url will be taken first)

  The major config for the router includes:
  
  serviceDict.mapping:
  router.hostWhitelist:


### Note:

If you want to use SidecarServiceDictHandler to get the service Id by the path url mapping from serviceDict.yml, add it before token handlers and router handler. The service Id get from serviceDict
will be used for next handler chain.
  
```
  - com.networknt.router.middleware.GatewayServiceDictHandler@path
  - com.networknt.router.middleware.GatewaySAMLTokenHandler@saml
  - com.networknt.router.GatewayRouterHandler@router

```




### start light-gateway locally and verify:

- start light-gateway service

```
cd ~/workspace
git clone git@github.com:networknt/light-gateway.git

cd light-gateway

mvn clean install


java -jar -Dlight-4j-config-dir=config/local  target/light-gateway.jar


```

The light-gateway service will start on http port 9080 and https port 9445. 

The service API could use any technologies, like NodeJs, .nets, php service...; The light-gateway service will handle the ingress and egress traffic to the pod and leverage light-4j cross-cutting concerns and client module features.



- Start Nodejs restful API (It is simulate the service in the Pod) 

Follow the [steps](nodeapp/start.md) to start Nodejs books store restful API. The Nodejs api will start on local port: 8080 

We can verify the Nodejs restful API directly with curl command:

```
Get:

curl --location --request GET 'http://localhost:8080/api/books/' \
--header 'Content-Type: application/json' \
--data-raw '{"name":"mybook"}'

Post:

curl --location --request POST 'http://localhost:8080/api/books/' \
--header 'Content-Type: application/json' \
--data-raw '{"title":"Newbook"}'

Put:

curl --location --request POST 'http://localhost:8080/api/books/' \
--header 'Content-Type: application/json' \
--data-raw '{"title":"Newbook"}'

Delete:

curl --location --request DELETE 'http://localhost:8080/api/books/4' \
--header 'Content-Type: application/json' \
```


- Start a sample light-4j API from light-example-4j (It is simulate the outside service which service in the Pod need to call):


```
 cd ~/networknt
 git clone git@github.com:networknt/light-example-4j.git
 cd ~/networknt/light-example-4j/servicemesher/services

 mvn clean install -Prelease

cd petstore-service-api

java -jar target/petstore-service-api-3.0.1.jar

```

The petstore light-api will start on local https 8443 port. 


- Try the call by using light-gateway:

#### Egress traffic (http protocol, port 9080)

Send request from service in the pod to light API petstore through light-gateway

```
curl --location --request GET 'http://localhost:9080/v1/pets' \
--header 'Content-Type: application/json' \
--data-raw '{"accountId":1,"transactioType":"DEPOSIT","amount":20}'
```

#### Ingress traffic (https protocol, port 9445)

Send request from outside service to the service in the pod through light-gateway

```
curl --location --request GET 'https://localhost:9445/api/books/' \
--header 'Content-Type: application/json' \
--data-raw '{"name":"mybook"}'
```

Leverage schema validation handler cross-cutting concerns

```
curl --location --request POST 'https://localhost:9445/api/books/' \
--header 'Content-Type: application/json' \
--data-raw '{"author":"Steve Jobs"}'
```

response:

```
{
    "statusCode": 400,
    "code": "ERR11004",
    "message": "VALIDATOR_SCHEMA",
    "description": "Schema Validation Error - requestBody.title: is missing but it is required",
    "severity": "ERROR"
}
```


