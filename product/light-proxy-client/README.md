To start the first instance. 

java -Xms200m -Xmx480m -Dlight-4j-config-dir=config1 -Dlogback.configurationFile=config1/logback.xml -jar ../../target/light-gateway.jar

To start the second instance.

java -Xms200m -Xmx480m -Dlight-4j-config-dir=config2 -Dlogback.configurationFile=config2/logback.xml -jar ../../target/light-gateway.jar
