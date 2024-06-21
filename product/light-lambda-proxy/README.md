The light-gateway can be used to proxy the HTTP request directly to a Lambda function on AWS.

The light-gateway can turn several Lambda functions into a Rest API. Each Lambda function will be an endpoint for the Rest API and the request will be validated on the light-gateway against the openapi.yaml specification. In fact, the Lambda functions should be generated from the same specification as well.

The current demo configuration is to access the [lambda-market](https://github.com/networknt/lambda-market) post Lambda MarketStoreProductsPostFunction. The entire project is generated from the light-codegen with the configuration in [model-config](https://github.com/networknt/model-config/tree/master/lambda/market) with some modifications.

The MarketStoreProductsPostFunction is changed in the configuration with timeout 2 minutes. The business handler has 1 minute sleep before response in order to test the following timeout configuration.

```
# lambda-invoker.yml
lambda-invoker.region: us-east-2
lambda-invoker.apiCallTimeout: 360000
lambda-invoker.apiCallAttemptTimeout: 120000
lambda-invoker.functions:
  /market/{store}/products@get: MarketStoreProductsGetFunction
  /market/{store}/products@post: MarketStoreProductsPostFunction

```

In order to invoke the lambda function, we need to update the values.yml to add a handler and change the lambda to proxy in the default chain.

```
handler.handlers:
  .
  .
  .
  - com.networknt.server.handler.ServerShutdownHandler@shutdown
  - com.networknt.aws.lambda.LambdaFunctionHandler@lambda

handler.chains.default:
  .
  .
  .
  - validator
  - lambda
```

To test, send the following request.

```
curl --location --request POST 'https://localhost:8443/market/12345/products' \
--header 'Content-Type: application/json' \
--data-raw '{"id":1,"name":"product1"}'
```

After 1 minute, the response will return.

```
{
    "id": 0,
    "name": "product0",
    "price": 100,
    "description": "This is a product description"
}
```
