This is an example configuration for [external access point](https://doc.networknt.com/service/gateway/external-access-point/) usage of light-gateway. Basically it is a micro-gateway for third-party consumers to access internal or external APIs controlled by an organization. 

In this example, we are going to expose two externall APIs with updated paths with URL rewriting. We aslo set up an Okta instance to protect the API with client credentials token. The two API endpoints are public without any protection. 

Here is the detail about the three APIs:

### PetStore

https://localhost:9443/v1/pets

### Cat Facts

https://catfact.ninja/fact

### REST API Example

https://dummy.restapiexample.com/api/v1/employees


We are going to rewrite the url for the above APIs to /v1/cats and /v1/employees. The /v1/pets is the same as the downstream API so there is no need to rewrite the URL. 

If your organization needs an http gateway to access external API, you have to use the external service with proxy config and also the client module will need to set up the proxy. 

You can also create an openapi.yaml specification file that include all the endpoints for validation and scope validation for security. 


Here is a tutorial that walk through the example. 

[External Access Point](https://youtu.be/h0fGpd-u6D0)

