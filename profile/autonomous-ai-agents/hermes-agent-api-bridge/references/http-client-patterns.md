# Client Integration Patterns

## Python Client Library

```python
import requests

class HermesClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def chat(self, prompt, session_id=None, skills=None, timeout=300):
        payload = {"prompt": prompt}
        if session_id: payload["session_id"] = session_id
        if skills: payload["skills"] = skills
        resp = requests.post(f"{self.base_url}/chat",
            json=payload, headers=self.headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            resp = requests.post(f"{self.base_url}/files/in",
                files={"file": f}, headers=self.headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def download_file(self, filename, save_path):
        resp = requests.get(f"{self.base_url}/files/out/{filename}",
            headers=self.headers, stream=True, timeout=120)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return save_path

    def health(self):
        return requests.get(f"{self.base_url}/health", timeout=10).json()

    def list_sessions(self):
        resp = requests.get(f"{self.base_url}/sessions",
            headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
```

### Usage

```python
client = HermesClient("http://192.168.1.100:8000", token="your-token")

# Stateful conversation
r1 = client.chat("Perform brainstorming for a new product")
r2 = client.chat("Narrow to top 3", session_id=r1["session_id"])

# File operations
client.upload_file("/path/to/data.xlsx")
r3 = client.chat("Analyze the uploaded sales data and summarize")
client.download_file("summary.xlsx", "/local/path/summary.xlsx")
```

## ChainLit Integration

```python
import chainlit as cl
from hermes_client import HermesClient

HERMES_URL = "http://127.0.0.1:8000"
HERMES_TOKEN = "your-token"

@cl.on_chat_start
async def start():
    client = HermesClient(HERMES_URL, token=HERMES_TOKEN)
    cl.user_session.set("hermes_client", client)
    cl.user_session.set("hermes_session_id", None)

@cl.on_message
async def main(message: cl.Message):
    client = cl.user_session.get("hermes_client")
    session_id = cl.user_session.get("hermes_session_id")
    result = client.chat(prompt=message.content, session_id=session_id)
    if result["success"]:
        cl.user_session.set("hermes_session_id", result["session_id"])
        await cl.Message(content=result["response"]).send()
    else:
        await cl.Message(content=f"Error: {result.get('error')}").send()
```

## Android Kotlin Client (HTTP thin client)

```kotlin
class HermesApiClient(
    private val serverUrl: String,
    private val authToken: String
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(600, TimeUnit.SECONDS).build()
    private val jsonMedia = "application/json".toMediaType()

    data class ChatResponse(
        val response: String, val sessionId: String?,
        val success: Boolean, val error: String?
    )

    fun chat(prompt: String, sessionId: String? = null,
             skills: List<String>? = null): ChatResponse {
        val payload = JSONObject().apply {
            put("prompt", prompt)
            sessionId?.let { put("session_id", it) }
            skills?.let { put("skills", it) }
        }
        val request = Request.Builder()
            .url("$serverUrl/chat")
            .header("Authorization", "Bearer $authToken")
            .post(payload.toString().toRequestBody(jsonMedia))
            .build()

        client.newCall(request).execute().use { response ->
            val json = JSONObject(response.body!!.string())
            return ChatResponse(
                response = json.optString("response"),
                sessionId = json.optString("session_id"),
                success = json.optBoolean("success"),
                error = json.optString("error")
            )
        }
    }
}
```

### Android usage (off main thread)

```kotlin
val hermes = HermesApiClient("http://192.168.1.100:8000", "your-token")

lifecycleScope.launch(Dispatchers.IO) {
    val result = hermes.chat("Perform brainstorming for a new app idea")
    withContext(Dispatchers.Main) {
        if (result.success) {
            textView.text = result.response
            currentSessionId = result.sessionId
        }
    }
}
```

## curl Examples

```bash
SERVER="http://192.168.1.100:8000"
TOKEN="your-token"
AUTH="Authorization: Bearer $TOKEN"

# Health check
curl -s -H "$AUTH" "$SERVER/health" | jq .

# Simple chat (new session)
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$SERVER/chat" -d '{"prompt": "What is 2+2?"}' | jq .

# Chat with skills
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$SERVER/chat" -d '{"prompt": "Create a plan", "skills": ["plan"]}' | jq .

# Stateful follow-up
SESSION="20260725_xxxx"
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$SERVER/chat" -d "{\"prompt\": \"Expand\", \"session_id\": \"$SESSION\"}" | jq .

# Upload file
curl -s -X POST -H "$AUTH" "$SERVER/files/in" -F "file=@data.xlsx" | jq .

# Download file
curl -s -H "$AUTH" -o summary.xlsx "$SERVER/files/out/summary.xlsx"
```
