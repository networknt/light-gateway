This is the proxy to the petstore API to test two rule action classes in one request transformer.

The request will be json and it is converted to xml in the first plugin with generic-rest2soap.
The second rule will add the security header in the xml with soap-security plugin.

This configuration is also used to test the token-limit for OAuth 2.0 provider proxy.
