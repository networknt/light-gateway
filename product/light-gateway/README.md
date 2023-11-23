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

In my .profile, I have the following line to set the environment variable.

```
export CONFIG_SERVER_CLIENT_TRUSTSTORE_LOCATION=/home/steve/networknt/light-4j/server/src/main/resources/config/bootstrap.truststore
export CONFIG_SERVER_CLIENT_TRUSTSTORE_PASSWORD=password
export CONFIG_SERVER_CLIENT_VERIFY_HOST_NAME=false
export CONFIG_SERVER_AUTHORIZATION="Bearer eyJraWQiOiIxMDAiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJ1cm46Y29tOm5ldHdvcmtudDpvYXV0aDI6djEiLCJhdWQiOiJ1cm46Y29tLm5ldHdvcmtudCIsImV4cCI6MTk0NDA1NzIxNiwianRpIjoiclFqUUhXX3ZJaEE3Z3pQazA4bjhfQSIsImlhdCI6MTYyODY5NzIxNiwibmJmIjoxNjI4Njk3MDk2LCJ2ZXJzaW9uIjoiMS4wIiwiY2xpZW50X2lkIjoiZjdkNDIzNDgtYzY0Ny00ZWZiLWE1MmQtNGM1Nzg3NDIxZTcyIiwic2NvcGUiOiJwb3J0YWwuciBwb3J0YWwudyIsInNlcnZpY2UiOiJleGFtcGxlLXNlcnZpY2UifQ.Kyz8mlOeStLJC1qNZQAJWRB-MsZEZcq-7lW3XARcw4ttijCsLnh4iCydVK_TZCYlBUMG3-V06yfHWaZsZG7vLqhri9YnxRJkUpkl__Phmba3sMcXnaVydjNYlIJBQMYl0Cn49lMUpvryldDRiVbDzyhejZwA_xn4mxbKcjD0wTaAOWOPQ7MuZie_m1xcKl0qEsznPBpI1MRBVsBC1Dmc5lnrt7dh3d-Q2zpdxYYv4k7V9uC2vDmtfUg8hgk4VaxZICWI2j_7zbhBUh-MTcE2tGCT-yrvDy_NgIvmMG3HcGjaZk7m91g-_0l-BENx9CEcaB0fimHClSPlx8Mci1THpQ"
export LIGHT_ENV=dev
```
