#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: bash images/rundinova/build-overlay.sh <local-base-image> <new-release-tag>" >&2
  echo "Example: bash images/rundinova/build-overlay.sh rundinova/erpnext:16.37.7-rn.25-navigation-assets 16.37.7-rn.26-next-change" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

base_image="$1"
release_tag="$2"
target_image="rundinova/erpnext:${release_tag}"

case "$base_image" in
rundinova/erpnext:* | rundinova/erpnext@sha256:*) ;;
*)
  echo "Base must be an approved local rundinova/erpnext image or digest." >&2
  exit 2
  ;;
esac

if [[ "$base_image" == *:latest || "$base_image" == *-latest ]]; then
  echo "Moving tags such as latest are not valid release bases." >&2
  exit 2
fi

if [[ ! "$release_tag" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ || "$release_tag" == latest ]]; then
  echo "Release tag must be a unique immutable tag without spaces or slashes." >&2
  exit 2
fi

if ! docker image inspect "$base_image" >/dev/null 2>&1; then
  echo "Base image is not present locally: $base_image" >&2
  echo "This builder never pulls a base or updates Frappe/ERPNext from upstream." >&2
  exit 1
fi

if docker image inspect "$target_image" >/dev/null 2>&1; then
  echo "Refusing to overwrite existing release image: $target_image" >&2
  exit 1
fi

base_id="$(docker image inspect --format '{{.Id}}' "$base_image")"
source_commit="${RUNDINOVA_SOURCE_COMMIT:-$(git rev-parse HEAD)}"
echo "Building app-only candidate: $target_image"
echo "Pinned local base: $base_image ($base_id)"
echo "RundiNova source commit: $source_commit"

docker build \
  --pull=false \
  --build-arg="RUNDINOVA_BASE_IMAGE=${base_image}" \
  --build-arg="RUNDINOVA_BASE_IMAGE_ID=${base_id}" \
  --build-arg="RUNDINOVA_SOURCE_COMMIT=${source_commit}" \
  --tag="$target_image" \
  --file=images/rundinova/Overlay.Containerfile .

echo "Candidate image ID: $(docker image inspect --format '{{.Id}}' "$target_image")"
echo "The running stack was not changed. Promote this tag only through the release procedure."
