#!/usr/bin/env bash
set -euo pipefail

usage() {
	echo "Usage: bash images/rundinova/publish-image.sh <local-image> <immutable-ghcr-image>" >&2
	echo "Example: bash images/rundinova/publish-image.sh rundinova/erpnext:16.37.7-rn.72-production-no-default-password ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.72-production-no-default-password" >&2
}

if [[ $# -ne 2 ]]; then
	usage
	exit 2
fi

source_image="$1"
target_image="$2"

case "$source_image" in
	rundinova/erpnext:*) ;;
	*) echo "Source must be a local rundinova/erpnext release image." >&2; exit 2 ;;
esac

case "$target_image" in
	ghcr.io/jubuniyokodev/rundinova-erpnext:*) ;;
	*) echo "Target must use the RundiNova GHCR package and an immutable release tag." >&2; exit 2 ;;
esac

release_tag="${target_image##*:}"
if [[ ! "$release_tag" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ || "$release_tag" == latest ]]; then
	echo "Release tag must be unique, immutable, and must not be latest." >&2
	exit 2
fi

if ! docker image inspect "$source_image" >/dev/null 2>&1; then
	echo "Source image is not present locally: $source_image" >&2
	exit 1
fi

image_id="$(docker image inspect --format '{{.Id}}' "$source_image")"
if docker image inspect "$target_image" >/dev/null 2>&1; then
	target_id="$(docker image inspect --format '{{.Id}}' "$target_image")"
	if [[ "$target_id" != "$image_id" ]]; then
		echo "Refusing to replace a different local image at the release tag: $target_image" >&2
		exit 1
	fi
else
	docker tag "$source_image" "$target_image"
fi

if ! command -v gh >/dev/null 2>&1; then
	echo "GitHub CLI is required to authenticate to GHCR without exposing a token." >&2
	exit 1
fi

github_user="$(gh api user --jq .login)"
rundi_docker_config="$(mktemp -d)"
trap 'rm -rf "$rundi_docker_config"' EXIT
export DOCKER_CONFIG="$rundi_docker_config"

echo "Authenticating $github_user to GHCR using the GitHub CLI credential."
gh auth token | docker login ghcr.io --username "$github_user" --password-stdin

echo "Publishing $source_image ($image_id) as $target_image"
docker push "$target_image"
