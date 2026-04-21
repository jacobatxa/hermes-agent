#!/bin/bash
set -e

HERMES_HOME="${HERMES_HOME:-/opt/data}"
INSTALL_DIR="/opt/hermes"

# Ensure pip-installed scripts (like `hermes`) are in PATH
export PATH="/usr/local/bin:$PATH"

mkdir -p "$HERMES_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# ALWAYS copy the correct config from the image (overwrite stale volume copies)
if [ -f "$INSTALL_DIR/zeabur-deploy/config.yaml" ]; then
    cp "$INSTALL_DIR/zeabur-deploy/config.yaml" "$HERMES_HOME/config.yaml"
    echo "[entrypoint] config.yaml synced from image"
elif [ ! -f "$HERMES_HOME/config.yaml" ]; then
    cp "$INSTALL_DIR/cli-config.yaml.example" "$HERMES_HOME/config.yaml" 2>/dev/null || true
fi

# Copy .env if not present
if [ ! -f "$HERMES_HOME/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$HERMES_HOME/.env" 2>/dev/null || true
fi

# Decode AUTH_JSON_B64 env var into auth.json (for Nous OAuth tokens)
if [ -n "$AUTH_JSON_B64" ]; then
    echo "$AUTH_JSON_B64" | base64 -d > "$HERMES_HOME/auth.json" 2>/dev/null
    echo "[entrypoint] auth.json decoded from AUTH_JSON_B64 env var"
elif [ ! -f "$HERMES_HOME/auth.json" ]; then
    # Try to copy from image if present
    if [ -f "$INSTALL_DIR/auth.json" ]; then
        cp "$INSTALL_DIR/auth.json" "$HERMES_HOME/auth.json"
    fi
fi

# Sync bundled skills
if [ -d "$INSTALL_DIR/skills" ]; then
    python3 "$INSTALL_DIR/tools/skills_sync.py" 2>/dev/null || true
fi

echo "=== Hermes Gateway starting ==="
echo "HERMES_HOME: $HERMES_HOME"

# Prefer the installed `hermes` command, fall back to python3 -m
if command -v hermes >/dev/null 2>&1; then
    exec hermes "$@"
else
    echo "hermes command not found, using python3 -m hermes_cli fallback"
    exec python3 -m hermes_cli "$@"
fi
