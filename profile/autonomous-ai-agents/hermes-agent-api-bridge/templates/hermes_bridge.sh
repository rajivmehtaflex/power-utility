#!/data/data/com.termux/files/usr/bin/bash
# Shell wrapper for Hermes on Android/Termux — outputs JSON with session_id for Kotlin parsing.
#
# Place in Termux home: ~/hermes_bridge.sh
# Make executable: chmod +x ~/hermes_bridge.sh
#
# Called from Android app via RUN_COMMAND Intent.
# The Android app points EXTRA_COMMAND_PATH to this script instead of the hermes binary directly.
#
# Usage: ~/hermes_bridge.sh "your prompt here"
# Output: {"session_id":"20260725_xxxx","response":"...","exit":0}

PROMPT="$1"

# Run hermes, capture output
OUTPUT=$(hermes chat -q -z "$PROMPT" 2>/dev/null)
EXIT=$?

# Get the latest session ID for follow-up messages
SESSION_ID=$(hermes sessions list --format json 2>/dev/null | jq -r '.[0].id // empty')

# Output as JSON for easy parsing in Kotlin (JSONObject)
echo "{\"session_id\":\"$SESSION_ID\",\"response\":$(echo "$OUTPUT" | jq -Rs .),\"exit\":$EXIT}"
