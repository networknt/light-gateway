package com.networknt;

import com.networknt.config.Jackson2Defaults;
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
            for (var entry : Jackson2Defaults.mapper().readTree(json)) {
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
}
