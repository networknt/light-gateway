### Start Server
To start the light-gateway from command line.

```
java -Xms200m -Xmx480m -Dlight-4j-config-dir=config -Dlogback.configurationFile=config/logback.xml -jar ../../target/light-gateway.jar
```

To star the server from the Intellij IDEA, please specify the following JVM options.

```
-Dlight-4j-config-dir=product/light-gateway/config -Dlogback.configurationFile=product/light-gateway/logback.xml
```

And the following for the evn variable which point the config server to the light-portal gateway.

```
LIGHT_CONFIG_SERVER_URI=https://localhost:8443
```

The next environment variable that we need to add to the IDEA is the encrypt master key.

```
LIGHT_4J_CONFIG_PASSWORD=DEMOKEY
```

In my .profile, I have the following line to set the environment variable.

```
export CONFIG_SERVER_CLIENT_TRUSTSTORE_LOCATION=/home/steve/networknt/light-4j/server/src/main/resources/config/bootstrap.truststore
export CONFIG_SERVER_CLIENT_TRUSTSTORE_PASSWORD=password
export CONFIG_SERVER_CLIENT_VERIFY_HOST_NAME=false
export LIGHT_PORTAL_AUTHORIZATION="Bearer eyJ..."
export LIGHT_ENV=dev
```
