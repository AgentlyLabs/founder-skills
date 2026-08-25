#!/usr/bin/env bash
# Package each skill as a zip for upload to Claude Desktop / claude.ai.
#
# The archive has to contain the skill *folder* — SKILL.md one level down, not at
# the root of the zip. Zipping from inside the skill directory produces the wrong
# shape and the upload gets rejected, which is the most common reason this fails.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
command -v zip >/dev/null || { echo "error: \`zip\` not found."; exit 1; }

rm -rf "$DIST"; mkdir -p "$DIST"
cd "$ROOT/skills"

for dir in */; do
  name="${dir%/}"
  if [ ! -f "$name/SKILL.md" ]; then
    echo "  skip $name — no SKILL.md"
    continue
  fi
  zip -qr "$DIST/$name.zip" "$name" \
    -x '*.DS_Store' '*/__pycache__/*' '*.pyc'
  printf '  %-12s %s\n' "$name" "$(du -h "$DIST/$name.zip" | cut -f1)"
done

echo
echo "-> $DIST"
echo "Upload one at a time: Customize → Skills → + → Upload skill"
