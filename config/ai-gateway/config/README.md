This folder contains the configuration to start the light-gateway from the local config server. It is used to debug the config server API and also the startup sequence of the light-4j framework.

The bootstrap.truststore is just the default client.truststore as the config server uses the corresponding server.truststore. The startup.yml is used to set up the query parameters to access the config server endpoints.


The following is the option configuration for the server for the run/debug for IntelliJ Idea.

```
-Dlight-4j-config-dir=config/config-server -Dlogback.configurationFile=config/server-proxy-petstore/logback.xml
```

Also, set up the following environment variables.

```
LIGHT_4J_CONFIG_PASSWORD=DEV;LIGHT_CONFIG_SERVER_URI=https://localhost:8435;CONFIG_SERVER_CLIENT_TRUSTSTORE_LOCATION=/home/steve/networknt/light-gateway/config/config-server/bootstrap.truststore
```

The above is for IDE with dynamic properties.

There are some fixed properties, and we can define them in the .profile as environment variables.

```
export CONFIG_SERVER_CLIENT_TRUSTSTORE_PASSWORD=password
export CONFIG_SERVER_CLIENT_VERIFY_HOST_NAME=false
export CONFIG_SERVER_AUTHORIZATION="Bearer eyJ..."
export LIGHT_ENV=dev
```
