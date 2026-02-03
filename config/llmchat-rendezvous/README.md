# LLM Chat Rendezvous Configuration

This configuration folder enables the "Rendezvous" WebSocket pattern for the LLM Chat application using `light-gateway`.

In this pattern, the Gateway acts as a bridge. The client (browser) connects first and waits. Then, the client triggers the backend service via an HTTP endpoint, which causes the backend to connect back to the Gateway. The Gateway then bridges the two WebSocket connections.

## Directory Structure

- `config/`: Contains the server configuration files.
  - `values.yml`: Main configuration file.
    - Enables HTTP on port 9080.
    - Configures `WebSocketRouterHandler` for routing.
    - Configures `ProxyHandler` to route `/connect` requests to the backend (`http://localhost:9082`).
- `public/`: Contains the static web assets.
  - `index.html`: The chat UI. It includes logic to generate a `channelId`, connect to the WebSocket, and trigger the backend via the `/connect` endpoint.

## Usage

To start the Light Gateway with this configuration:

1.  **Build the projects** (if not already done):
    ```bash
    cd ~/networknt/light-gateway
    mvn clean install -DskipTests
    ```

2.  **Run the Gateway**:
    ```bash
    java -Dlight-4j-config-dir=config/llmchat-rendezvous/config -jar target/light-gateway.jar
    ```
    *Note: Adjust the path to `light-gateway.jar` as needed based on your build location.*

3.  **Start the Backend Service**:
    Ensure the `llmchat-callback` service is running on port 9082.
    ```bash
    cd ~/networknt/light-example-4j/websocket/llmchat-callback
    java -jar target/llmchat-callback-2.3.2-SNAPSHOT.jar
    ```

4.  **Access the Chat**:
    Open your browser to [http://localhost:9080](http://localhost:9080).

## Workflow

1.  **User** opens the page and clicks "Connect".
2.  **Browser** generates a unique `channelId`.
3.  **Browser** opens a WebSocket connection to `ws://localhost:9080/chat?channelId=...`.
    - The Gateway accepts this connection and places it in a "waiting" state.
4.  **Browser** sends an HTTP POST request to `http://localhost:9080/connect?channelId=...`.
5.  **Gateway** proxies this request to the Backend (`llmchat-callback`) at `http://localhost:9082/connect`.
6.  **Backend** receives the request and initiates a WebSocket connection to the Gateway at `ws://localhost:9080/connect?channelId=...`.
7.  **Gateway** matches the Backend's connection with the waiting Client connection using the `channelId`.
8.  **Gateway** bridges the two connections, allowing bidirectional communication.
