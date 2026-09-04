#!/usr/bin/env bash
# Create the documented GitHub Pre-release for an existing remote tag.
# Requires an authenticated `gh` CLI. Never accepts or prints a token.
set -euo pipefail

TAG="${1:-v0.1.0-alpha.2}"
NOTES="${2:-docs/releases/${TAG}.md}"
TITLE="Harness Core Portable ${TAG} — Local Memory & User Control Foundations"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not installed. Install it from https://cli.github.com/ and run: gh auth login" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated. Run 'gh auth login' yourself; do not paste tokens into this script." >&2
  exit 1
fi
if ! git rev-parse --verify --quiet "refs/tags/${TAG}" >/dev/null; then
  echo "Local tag does not exist: ${TAG}" >&2
  exit 1
fi
if ! git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "Remote tag does not exist on origin: ${TAG}" >&2
  exit 1
fi
if [[ ! -f "$NOTES" ]]; then
  echo "Release notes file does not exist: ${NOTES}" >&2
  exit 1
fi
if gh release view "$TAG" >/dev/null 2>&1; then
  echo "A GitHub Release already exists for ${TAG}; refusing to create a duplicate." >&2
  echo "Review it first, then use 'gh release edit' explicitly if an update is intended." >&2
  exit 1
fi

gh release create "$TAG" \
  --title "$TITLE" \
  --notes-file "$NOTES" \
  --prerelease \
  --verify-tag

echo "Pre-release created for ${TAG}. Verify with: gh release view ${TAG} --json url,isPrerelease,tagName,name"
