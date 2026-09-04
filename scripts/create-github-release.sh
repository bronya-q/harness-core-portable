#!/usr/bin/env bash
# Create a GitHub Pre-release for a tag (requires `gh` CLI and auth).
set -euo pipefail
TAG="${1:-v0.1.0-alpha.2}"
NOTES="${2:-RELEASE_NOTES.md}"
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not installed. Install from https://cli.github.com/"
  exit 1
fi
gh release create "$TAG" --title "Harness Core Portable $TAG" --notes-file "$NOTES" --prerelease
echo "Pre-release created for $TAG"
