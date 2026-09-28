#!/bin/bash
# Sign the generated shortcuts so iPhone/iPad/Mac will import them.
# Run on a Mac signed in to iCloud:   ./sign_shortcuts.sh
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v shortcuts >/dev/null; then
  echo "The 'shortcuts' command is missing — this must run on macOS 12 or newer." >&2
  exit 1
fi
python3 build_shortcuts.py
mkdir -p signed
for f in unsigned/*.shortcut; do
  name="$(basename "$f")"
  echo "Signing $name"
  shortcuts sign --mode anyone --input "$f" --output "signed/$name"
done
echo "Done. Double-click each file in ./signed to import (Setup first)."
open signed
