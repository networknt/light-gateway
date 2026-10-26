package com.networknt;

import com.networknt.jackson.JacksonDefaults;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class GatewayNativeMetadataTest {
    @Test
    void nativeMetadataUsesLoadableJackson3TypesAndBundledSchemaMetadata() throws Exception {
        try (var input = getClass().getResourceAsStream("/META-INF/native-image/reflect-config.json")) {
            assertNotNull(input);
            String json = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            assertFalse(json.contains("com.fasterxml.jackson"));
            assertFalse(json.contains("Java7HandlersImpl"));
            assertFalse(json.contains("Java7SupportImpl"));
            assertFalse(json.contains("com.networknt.client.OAuthSignConfig"),
                    "client-config owns OAuthSignConfig native metadata");
            for (var entry : JacksonDefaults.mapper().readTree(json)) {
                String name = entry.get("name").asString();
                if (name.contains("tools.jackson"))
                    assertNotNull(Class.forName(name, false, getClass().getClassLoader()), name);
                assertFalse(name.startsWith("com.networknt.schema."),
                        "Schema validator supplies its own versioned native metadata");
            }
        }
        assertNotNull(getClass().getResource(
                "/META-INF/native-image/com.networknt/json-schema-validator/reflect-config.json"));
    }

    @Test
    void clientModuleRegistersItsPrivatePrimitiveSetter() throws Exception {
        try (var input = getClass().getResourceAsStream(
                "/META-INF/native-image/com.networknt/client-config/reflect-config.json")) {
            assertNotNull(input);
            boolean registered = false;
            for (var entry : JacksonDefaults.mapper().readTree(input)) {
                if (!"com.networknt.client.OAuthSignConfig".equals(entry.path("name").asString())) continue;
                for (var method : entry.path("methods")) {
                    var types = method.path("parameterTypes");
                    if ("setEnableHttp2".equals(method.path("name").asString())
                            && types.size() == 1 && "boolean".equals(types.get(0).asString())) registered = true;
                }
            }
            assertTrue(registered, "client-config must register the private primitive setter");
        }
    }
}
