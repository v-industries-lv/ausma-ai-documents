# RemoteRunner Backend API Documentation (BETA)

This is a documentation on what the RemoteRunner expects from remote backend api. 
This can be used for custom AI integrations, when the regular LLM runners are not enough. 

---

## Model Management Endpoints

### 1. List Models

*   **Endpoint:** `/api/models/list`
*   **Method:** `GET`
*   **Description:** Retrieves a list of all available models on the system.
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** An array of model names (strings).
    ```json
    [
        "model_name_1",
        "model_name_2",
        "model_name_3"
    ]
    ```

### 2. Show Model Details

*   **Endpoint:** `/api/models/show`
*   **Method:** `GET`
*   **Description:** Retrieves detailed information for a specific model.
*   **Query Parameters:** 
    *   `model`: The name of the model to retrieve.
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** Model details.
    ```json
    {
        "model": "model_thinking",
        "capabilities": [
            "completion",
            "thinking"
        ]
    }
    ```
*   **Error Response (404 Not Found):**
    *   **Body:** 
    ```json
    {
        "status": "error",
        "content": "Model not found"
    }
    ```

### 3. Pull Model

*   **Endpoint:** `/api/models/pull`
*   **Method:** `POST`
*   **Description:** Requests to pull a new model.
*   **Request Body:**
    *   Requires a JSON body containing the `model` name.
    ```json
    {
        "model": "model_to_add_name"
    }
    ```
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** 
    ```json
    true
    ```
*   **Failure Response (400/500 Error):**
    *   **Body:** 
    ```json
    false
    ```

### 4. Remove Model

*   **Endpoint:** `/api/models/remove`
*   **Method:** `POST`
*   **Description:** Requests model removal.
*   **Request Body:**
    *   Requires a JSON body containing the `model` name.
    ```json
    {
        "model": "model_to_remove_name"
    }
    ```
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** 
    ```json
    true
    ```
*   **Failure Response (400/500 Error):**
    *   **Body:** 
    ```json
    false
    ```

---

## Embedding Generation

*   **Endpoint:** `/api/embed`
*   **Method:** `POST`
*   **Description:** Generates embedding vectors for a list of inputs using a specified model.
*   **Request Body:**
    *   Requires a JSON body containing:
        *   `inputs`: An array of strings (the texts to embed).
        *   `model`: The model to use.
    ```json
    {
        "inputs": ["text one", "text two"],
        "model": "embedding_model"
    }
    ```
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** An object containing the generated embeddings.
    ```json
    {
        "embeddings": [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ]
    }
    ```
*   **Error Response (400 Bad Request):**
    *   **Body:** 
    ```json
    {
        "status": "error",
        "content": "Missing embedding model!"
    }
    ```

---

## Text Generation (Completion)

*   **Endpoint:** `/api/generate`
*   **Method:** `POST`
*   **Description:** Generates text content based on the model and message history. This endpoint supports both synchronous responses and streaming responses.
*   **Request Body:**
    *   Requires a JSON body containing:
        *   `model`: The model to use (e.g., `"test_model"`).
        *   `messages`: An array representing the conversation history (e.g., `[{"role": "user", "content": "Hi"}]`).
        *   `stream`: (Optional boolean) If `true`, the response will be streamed.

### Streaming Mode (Used for Chat UI)

*   **Condition:** Set `"stream": true` in the request body.
*   **Response Type:** `text/event-stream`
*   **Behavior:** The API streams data chunk by chunk, formatted as SSE events.
*   **Example Stream Output:**
    ```text
    data: {"status": "generating", "content": "Once"}

    data: {"status": "generating", "content": " upon"}
    
    data: {"status": "generating", "content": " a"}
    
    data: {"status": "generating", "content": " time"}

    ... (more chunks) ...

    data: {"status": "done"}
    ```

### Standard Mode (Non-Streaming)

*   **Condition:** Set `"stream": false` or omit the `stream` key.
*   **Response Type:** `application/json`
*   **Success Response (200 OK):**
    ```json
    {
        "status": "done",
        "content": "This is simple completion text."
    }
    ```

**Error Handling:**

*   If errors are encountered, the API returns an error response:
    ```json
    {
        "status": "error",
        "content": "Error: invalid model."
    }
    ```
