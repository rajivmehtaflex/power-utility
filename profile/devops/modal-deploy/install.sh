#!/usr/bin/env bash
set -e

echo "🚀 Installing modal-deploy skill..."

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Fetch repository
echo "📥 Downloading..."
if command -v gh &> /dev/null; then
    gh repo clone rajivmehtaflex/modal-deploy "$TMP_DIR/skill" -- --depth 1
    rm -rf "$TMP_DIR/skill/.git"
else
    echo "⚠️  gh CLI not found, using curl..."
    curl -fsSL https://github.com/rajivmehtaflex/modal-deploy/archive/refs/heads/main.tar.gz | tar xz -C "$TMP_DIR"
    mv "$TMP_DIR/modal-deploy-main" "$TMP_DIR/skill"
fi

# Detect which agent(s) are installed and install to all matching locations
INSTALLED=0

# --- npx skills add (preferred for Claude Code, Codex, Antigravity) ---
if command -v npx &> /dev/null; then
    echo ""
    echo "📦 Installing via npx skills add..."
    npx skills add rajivmehtaflex/modal-deploy -y 2>/dev/null && INSTALLED=1 || true
fi

# --- Hermes Agent ---
HERMES_DEST=~/.hermes/skills/mlops/modal-deploy
if [ -d ~/.hermes/skills ]; then
    echo "📦 Installing for Hermes Agent..."
    mkdir -p "$(dirname "$HERMES_DEST")"
    rm -rf "$HERMES_DEST"
    cp -r "$TMP_DIR/skill" "$HERMES_DEST"
    echo "  ✅ Installed at $HERMES_DEST"
    INSTALLED=1
fi

# --- Claude Code ---
CLAUDE_DEST=~/.claude/skills/modal-deploy
if [ -d ~/.claude ] || command -v claude &> /dev/null; then
    echo "📦 Installing for Claude Code..."
    mkdir -p "$(dirname "$CLAUDE_DEST")"
    rm -rf "$CLAUDE_DEST"
    cp -r "$TMP_DIR/skill" "$CLAUDE_DEST"
    echo "  ✅ Installed at $CLAUDE_DEST"
    INSTALLED=1
fi

# --- Codex ---
CODEX_DEST=~/.codex/skills/modal-deploy
if [ -d ~/.codex ] || command -v codex &> /dev/null; then
    echo "📦 Installing for Codex..."
    mkdir -p "$(dirname "$CODEX_DEST")"
    rm -rf "$CODEX_DEST"
    cp -r "$TMP_DIR/skill" "$CODEX_DEST"
    echo "  ✅ Installed at $CODEX_DEST"
    INSTALLED=1
fi

# Fallback: if no agent detected, suggest npx skills add
if [ "$INSTALLED" -eq 0 ]; then
    echo ""
    echo "⚠️  No supported agent detected."
    echo "   Install with: npx skills add rajivmehtaflex/modal-deploy"
    exit 1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage: The skill will auto-activate when you ask about Modal deployment,"
echo "       GPU configuration, or cloud deployment in your AI agent."
