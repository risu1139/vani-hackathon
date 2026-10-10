#!/bin/bash
# install_vani.sh: root-owned install of the vani-persona skill on the Daytona sandbox (run with sudo by deploy.py).
# Peer review (Redash skill, 2026-10-10), blockers fixed here:
#   1. the agent runs as a SEPARATE user (vaniagent) with no sudo; `daytona` keeps sudo for setup only;
#   2. Claude Code is installed root-owned and pinned (/opt/claude-code, /usr/local/bin/claude), not in a user dir;
#   3. every hook runs /usr/bin/python3.13 -E -s (no PYTHON* env, no user site dir -> no planted .pth files);
#   5. the staged tarball is verified against the laptop's sha256 before anything is extracted as root.
# Settings live under /usr/local/share (not /etc/claude-code), so interactive claude sessions are not affected.
#
# Usage: sudo bash install_vani.sh <stage.tgz> <sha256>
set -euo pipefail
TGZ="${1:?stage tarball}"
SHA="${2:?expected sha256}"
DEST=/usr/local/share/vani-persona
PY=/usr/bin/python3.13
AGENT=vaniagent
CLAUDE_VERSION=2.1.296
NPM=/usr/local/nvm/versions/node/v22.14.0/bin/npm

echo "$SHA  $TGZ" | sha256sum -c - || { echo "REFUSED: stage tarball sha256 mismatch"; exit 2; }
STAGE="$(mktemp -d)"
chmod 700 "$STAGE"
tar xzf "$TGZ" -C "$STAGE"

# 1. the agent user: no sudo, no sudoers entry, not in the sudo group
id "$AGENT" >/dev/null 2>&1 || useradd -m -s /bin/bash "$AGENT"
gpasswd -d "$AGENT" sudo >/dev/null 2>&1 || true
rm -f "/etc/sudoers.d/$AGENT"
if sudo -l -U "$AGENT" 2>/dev/null | grep -q "may run"; then echo "REFUSED: $AGENT has sudo rights"; exit 2; fi
# nothing may come back on its own: no cron, no at, no lingering user services (peer review MUST 1)
for f in /etc/cron.deny /etc/at.deny; do touch "$f"; grep -qx "$AGENT" "$f" || echo "$AGENT" >> "$f"; done
command -v loginctl >/dev/null && loginctl disable-linger "$AGENT" 2>/dev/null || true
chmod 700 "/home/$AGENT"

# 2. root-owned, pinned Claude Code
if [ "$(/usr/local/bin/claude --version 2>/dev/null | cut -d' ' -f1)" != "$CLAUDE_VERSION" ]; then
  rm -rf /opt/claude-code
  PATH="$(dirname "$NPM"):$PATH" "$NPM" install -g --prefix /opt/claude-code "@anthropic-ai/claude-code@$CLAUDE_VERSION" >/dev/null
  ln -sf /opt/claude-code/bin/claude /usr/local/bin/claude
fi
chown -R root:root /opt/claude-code
chmod -R go-w /opt/claude-code

# the skill + the 3 repo files it reads, root-owned
rm -rf "$DEST"
mkdir -p "$DEST/skill" "$DEST/repo/app/contracts" "$DEST/repo/app/sarvam" "$DEST/repo/outputs"
cp -r "$STAGE/skill/." "$DEST/skill/"
rm -rf "$DEST/skill/tests"
find "$DEST" -name "__pycache__" -type d -prune -exec rm -rf {} +
cp "$STAGE/app/contracts/sarvam_vars.contract.json" "$DEST/repo/app/contracts/"
cp "$STAGE/app/sarvam/vani_prompt.md" "$DEST/repo/app/sarvam/"
[ -f "$STAGE/outputs/objections.json" ] && cp "$STAGE/outputs/objections.json" "$DEST/repo/outputs/"

# 3. settings: hooks with absolute python -E -s
cat > "$DEST/settings.json" <<EOF
{"hooks": {
 "PreToolUse": [{"matcher": "Write|Edit|MultiEdit|NotebookEdit", "hooks": [{"type": "command", "command": "$PY -E -s $DEST/skill/gates/pre_gate.py", "timeout": 10}]}],
 "Stop": [{"hooks": [{"type": "command", "command": "$PY -E -s $DEST/skill/gates/stop_gate.py", "timeout": 180}]}]}}
EOF
echo '{"mcpServers": {}}' > "$DEST/empty_mcp.json"
chown -R root:root "$DEST"
chmod -R go-w "$DEST"
chmod -R a+rX "$DEST"

# work dirs owned by the launcher (daytona). 711: the agent can enter its own run dir by name but cannot list others
# (peer review MUST 2); the seller staging dir on tmpfs is 700 (the agent never reads it; the launcher copies one seller in).
mkdir -p /srv/vani/runs /srv/vani/launcher /srv/vani/scoreboards /srv/vani/stubruns /dev/shm/vani/sellers
chown -R daytona:daytona /srv/vani /dev/shm/vani
chmod 711 /srv/vani /srv/vani/runs /srv/vani/launcher /srv/vani/stubruns
chmod 700 /srv/vani/scoreboards /dev/shm/vani /dev/shm/vani/sellers

rm -rf "$STAGE"
echo "installed: $DEST (root-owned); python=$PY; claude=$(/usr/local/bin/claude --version); agent user=$AGENT (no sudo)"
