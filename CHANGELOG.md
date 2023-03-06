# Change Log

## [2.1.8](https://github.com/networknt/light-gateway/tree/2.1.8) (2023-03-06)


**Merged pull requests:**


- fixes \#118 update server-proxy-petstore config to add oauth [\#119](https://github.com/networknt/light-gateway/pull/119) ([stevehu](https://github.com/stevehu))
- fixes \#116 move the test proxy config to values.yml [\#117](https://github.com/networknt/light-gateway/pull/117) ([stevehu](https://github.com/stevehu))
- fixes \#114 update configuration for test [\#115](https://github.com/networknt/light-gateway/pull/115) ([stevehu](https://github.com/stevehu))
## [2.1.7](https://github.com/networknt/light-gateway/tree/2.1.7) (2023-02-14)


**Merged pull requests:**


- fixes \#112 upgrade aws lambda dependencies [\#113](https://github.com/networknt/light-gateway/pull/113) ([stevehu](https://github.com/stevehu))
- fixes \#110 add a test case to ensure that path prefix based timeout i… [\#111](https://github.com/networknt/light-gateway/pull/111) ([stevehu](https://github.com/stevehu))


## [2.1.6](https://github.com/networknt/light-gateway/tree/2.1.6) (2023-02-06)


**Merged pull requests:**


- fixes \#108 add OPTIONS method to the handler.yml to handle the cors p… [\#109](https://github.com/networknt/light-gateway/pull/109) ([stevehu](https://github.com/stevehu))
- fixes \#106 udpate test case config to add post endpoint to interceptor [\#107](https://github.com/networknt/light-gateway/pull/107) ([stevehu](https://github.com/stevehu))


## [2.1.5](https://github.com/networknt/light-gateway/tree/2.1.5) (2023-01-04)


**Merged pull requests:**


- fixes \#104 change the router http2Enabled to false to reproduce the e… [\#105](https://github.com/networknt/light-gateway/pull/105) ([stevehu](https://github.com/stevehu))
- fixes \#102 update the client-gateway configuration to route the pesto… [\#103](https://github.com/networknt/light-gateway/pull/103) ([stevehu](https://github.com/stevehu))
- fixes \#100 add commons-codec and commons-text to pom.xml [\#101](https://github.com/networknt/light-gateway/pull/101) ([stevehu](https://github.com/stevehu))


## [2.1.4](https://github.com/networknt/light-gateway/tree/2.1.4) (2022-11-30)


**Merged pull requests:**


- fixes \#98 add product folder for light-balance configuation [\#99](https://github.com/networknt/light-gateway/pull/99) ([stevehu](https://github.com/stevehu))


## [2.1.3](https://github.com/networknt/light-gateway/tree/2.1.3) (2022-11-10)


**Merged pull requests:**


- fixes \#96 add shutdown endpoint to handler.yml and values.yml [\#97](https://github.com/networknt/light-gateway/pull/97) ([stevehu](https://github.com/stevehu))
- fixes \#94 add OAuthServer to the handler.yml and values.yml [\#95](https://github.com/networknt/light-gateway/pull/95) ([stevehu](https://github.com/stevehu))
- fixes \#92 add apikey handler to the client-proxy-transform config [\#93](https://github.com/networknt/light-gateway/pull/93) ([stevehu](https://github.com/stevehu))
- add script to compile to native executable [\#90](https://github.com/networknt/light-gateway/pull/90) ([neillin](https://github.com/neillin))
- fixes \#88 update local config to replace the ProxyBodyHandler with In… [\#89](https://github.com/networknt/light-gateway/pull/89) ([stevehu](https://github.com/stevehu))


## [2.1.2](https://github.com/networknt/light-gateway/tree/2.1.2) (2022-10-23)


**Merged pull requests:**


- fixes \#84 add basic-auth into the dependency in pom.xml [\#85](https://github.com/networknt/light-gateway/pull/85) ([stevehu](https://github.com/stevehu))
- fixes \#82 update handler.yml to remove adm for health and add admin c… [\#83](https://github.com/networknt/light-gateway/pull/83) ([stevehu](https://github.com/stevehu))
- fixes \#78 add ip-whitelist to the dependency [\#79](https://github.com/networknt/light-gateway/pull/79) ([stevehu](https://github.com/stevehu))
- fixes \#76 enable audit log for client-proxy-transform configuration [\#77](https://github.com/networknt/light-gateway/pull/77) ([stevehu](https://github.com/stevehu))
- fixes \#74 enable failed test cases as the bug is fixed [\#75](https://github.com/networknt/light-gateway/pull/75) ([stevehu](https://github.com/stevehu))
- fixes \#72 The source buffer is this buffer for get test case [\#73](https://github.com/networknt/light-gateway/pull/73) ([stevehu](https://github.com/stevehu))
- fixes \#70 update server-proxy-petstore config to use interceptor inst… [\#71](https://github.com/networknt/light-gateway/pull/71) ([stevehu](https://github.com/stevehu))
- fixes \#68 Add configuration for Cannex API security transformation [\#69](https://github.com/networknt/light-gateway/pull/69) ([stevehu](https://github.com/stevehu))
- fixes \#66 enable audit and update the RequestBodyInterceptor [\#67](https://github.com/networknt/light-gateway/pull/67) ([stevehu](https://github.com/stevehu))
- fixes \#64 upgrade yaml-rule to 1.0.1 in pom.xml [\#65](https://github.com/networknt/light-gateway/pull/65) ([stevehu](https://github.com/stevehu))
- fixes \#62 add jackson xml dependency and complete the JSON to XML tra… [\#63](https://github.com/networknt/light-gateway/pull/63) ([stevehu](https://github.com/stevehu))
- fixes \#60 update the config for proxy transform with request header t… [\#61](https://github.com/networknt/light-gateway/pull/61) ([stevehu](https://github.com/stevehu))
- fixes \#58 update gateway to support external jar to transform respons… [\#59](https://github.com/networknt/light-gateway/pull/59) ([stevehu](https://github.com/stevehu))
- fixes \#56 add configuration folder for the transformation [\#57](https://github.com/networknt/light-gateway/pull/57) ([stevehu](https://github.com/stevehu))
- fixes \#54 update service dict handler test case to use new method fro… [\#55](https://github.com/networknt/light-gateway/pull/55) ([stevehu](https://github.com/stevehu))
- fixes \#52 remove config.yml file from the src to use the default [\#53](https://github.com/networknt/light-gateway/pull/53) ([stevehu](https://github.com/stevehu))
- fixes \#50 remove openapi-security and openapi-validator from the default [\#51](https://github.com/networknt/light-gateway/pull/51) ([stevehu](https://github.com/stevehu))
- fixes \#48 remove packaged config files to use the module default ones [\#49](https://github.com/networknt/light-gateway/pull/49) ([stevehu](https://github.com/stevehu))
- fixes \#45 remove client.yml, server.yml and update info endpoint to l… [\#46](https://github.com/networknt/light-gateway/pull/46) ([stevehu](https://github.com/stevehu))
- fixes \#43 remove the dummy openapi.yaml from the src resource config … [\#44](https://github.com/networknt/light-gateway/pull/44) ([stevehu](https://github.com/stevehu))
- fixes \#41 remove the openapi-inject.yml and add the favicon to the va… [\#42](https://github.com/networknt/light-gateway/pull/42) ([stevehu](https://github.com/stevehu))
- fixes \#39 update local values.yml to move the security and other hand… [\#40](https://github.com/networknt/light-gateway/pull/40) ([stevehu](https://github.com/stevehu))
- fixes \#37 update the handler.yml and specification.yml in resources c… [\#38](https://github.com/networknt/light-gateway/pull/38) ([stevehu](https://github.com/stevehu))
- fixes \#35 update config folder to externalize handler.yml to values.yml [\#36](https://github.com/networknt/light-gateway/pull/36) ([stevehu](https://github.com/stevehu))
- fixes \#33 add salesforce.yml templete to the resources config folder [\#34](https://github.com/networknt/light-gateway/pull/34) ([stevehu](https://github.com/stevehu))


## [2.1.1](https://github.com/networknt/light-gateway/tree/2.1.1) (2022-04-26)


**Merged pull requests:**




## [2.1.0](https://github.com/networknt/light-router/tree/2.1.0) (2022-02-28)

**Merged pull requests:**
