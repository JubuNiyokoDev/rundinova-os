"""Capture non-secret source provenance for a RundiNova container image."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

APP_NAMES = ("frappe", "erpnext", "hrms", "crm", "rundinova_tech")
VERSION_PATTERN = re.compile(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


def app_version(bench_dir, app):
    init_file = bench_dir / "apps" / app / app / "__init__.py"
    if not init_file.is_file():
        return None
    match = VERSION_PATTERN.search(init_file.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def app_revision(bench_dir, app):
    app_dir = bench_dir / "apps" / app
    try:
        return subprocess.check_output(
            ["git", "-C", str(app_dir), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def source_digest(app_dir):
    digest = hashlib.sha256()
    for path in sorted(app_dir.rglob("*")):
        if (
            any(
                part in EXCLUDED_DIRS or part.endswith((".egg-info", ".dist-info"))
                for part in path.parts
            )
            or path.suffix == ".pyc"
        ):
            continue
        if not path.is_file():
            continue
        relative_path = path.relative_to(app_dir).as_posix().encode("utf-8")
        digest.update(relative_path)
        digest.update(b"\0")
        with path.open("rb") as source_file:
            for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def safe_repository(value):
    if not value:
        return None
    if "@" in value and "://" not in value:
        value = value.split("@", 1)[1].replace(":", "/", 1)
    parsed = urlsplit(value)
    if parsed.scheme and parsed.hostname:
        return f"{parsed.hostname}{parsed.path}".removesuffix(".git").rstrip("/")
    return value.removesuffix(".git").rstrip("/")


def manifest_refs(manifest_path):
    if not manifest_path or not manifest_path.is_file():
        return None, {}, {}

    manifest_bytes = manifest_path.read_bytes()
    entries = json.loads(manifest_bytes)
    if isinstance(entries, dict):
        entries = entries.get("apps", [])

    refs = {}
    repositories = {}
    for entry in entries:
        repository = entry.get("url") or entry.get("repo") or entry.get("path") or ""
        safe_repo = safe_repository(repository)
        app_name = safe_repo.rsplit("/", 1)[-1] if safe_repo else ""
        if app_name:
            repositories[app_name] = safe_repo
            refs[app_name] = next(
                (
                    entry[key]
                    for key in ("commit", "tag", "branch", "ref")
                    if entry.get(key)
                ),
                None,
            )
    return hashlib.sha256(manifest_bytes).hexdigest(), refs, repositories


def application_records(bench_dir, requested_refs=None, repositories=None):
    requested_refs = requested_refs or {}
    repositories = repositories or {}
    records = []
    for app in APP_NAMES:
        if not (bench_dir / "apps" / app).is_dir():
            continue
        record = {
            "name": app,
            "version": app_version(bench_dir, app),
            "revision": app_revision(bench_dir, app),
        }
        if app in requested_refs:
            record["requested_ref"] = requested_refs[app]
        if app in repositories:
            record["repository"] = repositories[app]
        if app == "rundinova_tech":
            record["source_sha256"] = source_digest(bench_dir / "apps" / app)
        records.append(record)
    return records


def write_metadata(output_path, metadata):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def capture_base(args):
    bench_dir = Path(args.bench_dir)
    manifest_digest, requested_refs, repositories = manifest_refs(
        Path(args.manifest) if args.manifest else None
    )
    requested_refs["frappe"] = args.frappe_ref
    repositories["frappe"] = safe_repository(args.frappe_path)
    metadata = {
        "schema_version": 1,
        "release_type": "framework-base",
        "framework_inputs": {
            "frappe_ref": args.frappe_ref,
            "frappe_repository": repositories["frappe"],
            "build_image": args.build_image,
            "runtime_image": args.runtime_image,
        },
        "apps_manifest_sha256": manifest_digest,
        "applications": application_records(bench_dir, requested_refs, repositories),
    }
    write_metadata(Path(args.output), metadata)


def capture_overlay(args):
    bench_dir = Path(args.bench_dir)
    output_path = Path(args.output)
    current_applications = application_records(bench_dir)
    if output_path.is_file():
        metadata = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        metadata = {
            "schema_version": 1,
            "release_type": "rundinova-overlay",
            "upstream_revisions_available": False,
            "applications": current_applications,
        }

    applications = metadata.setdefault("applications", [])
    custom_app = next(
        (
            record
            for record in current_applications
            if record["name"] == "rundinova_tech"
        ),
        None,
    )
    if custom_app:
        for index, record in enumerate(applications):
            if record.get("name") == "rundinova_tech":
                applications[index] = custom_app
                break
        else:
            applications.append(custom_app)
    for record in applications:
        if record.get("name") != "rundinova_tech":
            record["version"] = app_version(bench_dir, record["name"])

    upstream_apps = [
        record for record in applications if record.get("name") != "rundinova_tech"
    ]
    metadata["upstream_revisions_available"] = bool(upstream_apps) and all(
        record.get("revision") for record in upstream_apps
    )
    metadata["release_type"] = "rundinova-overlay"
    metadata["base_image"] = args.base_image
    metadata["base_image_id"] = args.base_image_id
    write_metadata(output_path, metadata)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    base = subparsers.add_parser("base")
    base.add_argument("--bench-dir", required=True)
    base.add_argument("--manifest")
    base.add_argument("--output", required=True)
    base.add_argument("--frappe-ref", required=True)
    base.add_argument("--frappe-path", required=True)
    base.add_argument("--build-image", required=True)
    base.add_argument("--runtime-image", required=True)
    base.set_defaults(handler=capture_base)

    overlay = subparsers.add_parser("overlay")
    overlay.add_argument("--bench-dir", required=True)
    overlay.add_argument("--output", required=True)
    overlay.add_argument("--base-image", required=True)
    overlay.add_argument("--base-image-id", required=True)
    overlay.set_defaults(handler=capture_overlay)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
