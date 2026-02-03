# LLM Chat Gateway Configuration

This configuration folder establishes a central WebSocket Gateway for the LLM Chat application.

In this setup, the Gateway acts as a standard **Forward Proxy/Router** for WebSocket connections.
1.  Clients connect to the Gateway at `wss://localhost:8443/chat`.
2.  The Gateway looks up the service associated with `/chat` (`com.networknt.llmchat-1.0.0`).
3.  The Gateway uses Service Discovery (Direct Registry in this config) to find the downstream service URL (`http://localhost:8080`).
4.  The Gateway establishes a WebSocket connection to the downstream service and proxies messages between the client and the service.

## Directory Structure

- `config/`: Contains the server configuration files.
  - `values.yml`: Main configuration file.
    - HTTPS enabled on port 8443.
    - `WebSocketRouterHandler` configured to route `/chat` to `com.networknt.llmchat-1.0.0`.
    - `DirectRegistry` configured to point `com.networknt.llmchat-1.0.0` to `http://localhost:8080`.
- `public/`: Contains static web assets (e.g., chat UI).

## Usage

To start the Light Gateway with this configuration:

1.  **Build the projects** (if not already done):
    ```bash
    cd ~/networknt/light-gateway
    mvn clean install -DskipTests
    ```

2.  **Run the Gateway**:
    ```bash
    java -Dlight-4j-config-dir=config/llmchat-gateway/config -jar target/light-gateway.jar
    ```

3.  **Start the Backend Service**:
    Ensure the `llmchat-server` is running on port 8080.
    ```bash
    cd ~/networknt/light-example-4j/websocket/llmchat-server
    java -jar target/llmchat-server-2.3.2-SNAPSHOT.jar
    ```

4.  **Access the Chat**:
    Open your browser to [https://localhost:8443](https://localhost:8443).

## Workflow

1.  **User** opens the page in the browser.
2.  **Browser** connects to `wss://localhost:8443/chat`.
3.  **Gateway** accepts the connection and determines the target service is `llmchat-server`.
4.  **Gateway** connects to `ws://localhost:8080/chat`.
5.  **Gateway** pipes all traffic between the Browser and `llmchat-server`.
