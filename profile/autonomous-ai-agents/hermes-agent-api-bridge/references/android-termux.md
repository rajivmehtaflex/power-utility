# Android On-Device Hermes via Termux + Intent IPC

Run Hermes Agent natively on an Android phone through Termux, with full agent loop, skills, and local LLM. No server, no client-server architecture — all IPC is Android Intent-based (same device, no network).

## Architecture

```
Android App (Kotlin/Java)
    │
    │  RUN_COMMAND Intent (Android IPC, NOT HTTP)
    │
    ▼
Termux (RunCommandService)
    │
    │  subprocess
    │
    ▼
Hermes Agent → Ollama (localhost:11434) → GGUF Model
```

**This is NOT client/server.** The Intent system is same-device inter-process communication. No ports, no HTTP, no network.

## Setup

### 1. Install Termux + Hermes + Ollama

```bash
# In Termux (from F-Droid, NOT Play Store):
pkg update && pkg upgrade -y
pkg install -y git python clang rust make pkg-config libffi openssl nodejs ripgrep ffmpeg

# Install Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Install Ollama
pkg install ollama -y
ollama serve &
ollama pull qwen3.5:4b

# Configure Hermes for local model
hermes config set model.provider custom
hermes config set model.default qwen3.5:4b
hermes config set model.base_url http://127.0.0.1:11434/v1
```

### 2. Enable external app access

```bash
echo "allow-external-apps=true" >> ~/.termux/termux.properties
termux-wake-lock
# Settings → Apps → Termux → Battery → Unrestricted
```

### 3. AndroidManifest.xml

```xml
<uses-permission android:name="com.termux.permission.RUN_COMMAND" />
<queries>
    <package android:name="com.termux" />
</queries>
<application ...>
    <service android:name=".HermesResultService" />
</application>
```

## The Intent Bridge (Kotlin)

```kotlin
fun askHermes(prompt: String, skills: List<String> = emptyList(),
              sessionId: String? = null, onResult: (HermesResult) -> Unit) {
    val args = mutableListOf("chat", "-q", "-z", "--max-turns", "20")
    for (skill in skills) { args.addAll(listOf("-s", skill)) }
    if (sessionId != null) { args.addAll(listOf("--resume", sessionId)) }
    args.add(prompt)

    val intent = Intent().apply {
        setClassName("com.termux", "com.termux.app.RunCommandService")
        action = "com.termux.RUN_COMMAND"
        putExtra("com.termux.RUN_COMMAND_PATH",
                 "/data/data/com.termux/files/usr/bin/hermes")
        putExtra("com.termux.RUN_COMMAND_ARGUMENTS", args.toTypedArray())
        putExtra("com.termux.RUN_COMMAND_WORKDIR",
                 "/data/data/com.termux/files/home")
        putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)
    }

    val resultIntent = Intent(context, HermesResultService::class.java)
    val pendingIntent = PendingIntent.getService(
        context, executionId++, resultIntent,
        PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_MUTABLE
    )
    intent.putExtra("com.termux.RUN_COMMAND_PENDING_INTENT", pendingIntent)
    ContextCompat.startForegroundService(context, intent)
}
```

## Result Receiver (Kotlin)

```kotlin
class HermesResultService : IntentService("HermesResultService") {
    override fun onHandleIntent(intent: Intent?) {
        val bundle = intent?.getBundleExtra("com.termux.EXTRA_PLUGIN_RESULT_BUNDLE") ?: return
        val stdout = bundle.getString("stdout", "")
        val stderr = bundle.getString("stderr", "")
        val exitCode = bundle.getInt("exitCode", -1)
        // Deliver to your app
    }
}
```

## Constraints

| Constraint | Detail |
|---|---|
| Result size limit | ~100KB per result (Termux truncates). Write large outputs to file. |
| armv8l (32-bit) | Hermes requires aarch64 (64-bit). Rust/maturin won't compile on 32-bit ARM. |
| Background kills | Use `termux-wake-lock` + battery optimization exemption. |
| Startup time | First call: ~3-5s. Subsequent calls in same session: faster. |
| No voice | `faster-whisper` has no Android wheels. TTS works via `termux-tts-speak`. |
| Comma in args | Use Java/Kotlin Intent extras (not `am` command) to avoid comma escaping issues. |

## Android 11+ Package Visibility

On SDK 30+, add `<queries>` to AndroidManifest.xml or the Intent will be blocked:
```xml
<queries>
    <package android:name="com.termux" />
</queries>
```

## Permission Grant

The user must manually grant permission:
```
Settings → Apps → [Your App] → Permissions → Additional permissions → 
Run commands in Termux environment
```

Just adding `<uses-permission>` to the manifest is NOT sufficient.

## Sources

- RUN_COMMAND Intent: https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent
- Hermes Termux docs: https://github.com/nousresearch/hermes-agent/blob/main/website/docs/getting-started/termux.md
- Android 11 visibility: https://github.com/termux/termux-app/issues/1932
