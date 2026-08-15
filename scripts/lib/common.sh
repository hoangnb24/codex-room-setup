#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

log() {
  printf '%s\n' "$*"
}

warn() {
  printf 'WARNING: %s\n' "$*" >&2
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is missing: $1"
}

render_home_tokens() {
  local source_path="$1"
  local destination_path="$2"
  python3 - "$source_path" "$destination_path" "$HOME" <<'PY'
from pathlib import Path
import sys

source, destination, home = map(Path, sys.argv[1:])
content = source.read_text()
destination.write_text(content.replace("@@HOME@@", str(home)))
PY
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

