"""Tests for reproducible, non-secret container release provenance."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "capture-release-metadata.py"
SPEC = importlib.util.spec_from_file_location("capture_release_metadata", SCRIPT)
METADATA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METADATA)


def create_app(bench_dir, name, version):
    app_dir = bench_dir / "apps" / name
    package_dir = app_dir / name
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )
    return app_dir


class TestReleaseMetadata(unittest.TestCase):
    def test_framework_base_has_no_moving_upstream_defaults(self):
        containerfile = (SCRIPT.parent / "Containerfile").read_text(encoding="utf-8")

        self.assertIn("ARG FRAPPE_BRANCH\n", containerfile)
        self.assertIn("ARG FRAPPE_BUILD_IMAGE\n", containerfile)
        self.assertIn("ARG FRAPPE_RUNTIME_IMAGE\n", containerfile)
        self.assertNotIn("ARG FRAPPE_BRANCH=version-16", containerfile)
        self.assertNotIn("ARG FRAPPE_BUILD_IMAGE=", containerfile)
        self.assertNotIn("ARG FRAPPE_RUNTIME_IMAGE=", containerfile)

    def test_repository_urls_are_sanitized(self):
        self.assertEqual(
            METADATA.safe_repository(
                "https://deploy-user:secret-token@github.com/acme/private.git"
            ),
            "github.com/acme/private",
        )
        self.assertEqual(
            METADATA.safe_repository("git@github.com:acme/private.git"),
            "github.com/acme/private",
        )

    def test_source_digest_ignores_generated_and_git_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "rundinova_tech"
            app_dir.mkdir()
            source = app_dir / "domain.py"
            source.write_text("RULE = 1\n", encoding="utf-8")
            initial = METADATA.source_digest(app_dir)

            for relative in (
                ".git/config",
                "node_modules/pkg/index.js",
                "__pycache__/domain.pyc",
                "build/generated.js",
            ):
                ignored = app_dir / relative
                ignored.parent.mkdir(parents=True, exist_ok=True)
                ignored.write_text("ignored", encoding="utf-8")
            self.assertEqual(METADATA.source_digest(app_dir), initial)

            source.write_text("RULE = 2\n", encoding="utf-8")
            self.assertNotEqual(METADATA.source_digest(app_dir), initial)

    def test_base_capture_hashes_manifest_without_copying_credentials(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bench_dir = root / "bench"
            create_app(bench_dir, "frappe", "16.1.0")
            create_app(bench_dir, "erpnext", "16.1.0")
            create_app(bench_dir, "rundinova_tech", "0.2.0")
            manifest = root / "apps.json"
            manifest_bytes = json.dumps(
                [
                    {
                        "url": "https://robot:secret@github.com/acme/erpnext.git",
                        "commit": "approved-sha",
                    }
                ]
            ).encode("utf-8")
            manifest.write_bytes(manifest_bytes)
            output = root / "release" / "release-metadata.json"

            METADATA.capture_base(
                SimpleNamespace(
                    bench_dir=bench_dir,
                    manifest=manifest,
                    output=output,
                    frappe_ref="version-16-approved",
                    frappe_path="https://robot:secret@github.com/frappe/frappe.git",
                    build_image="frappe/build@sha256:build-digest",
                    runtime_image="frappe/base@sha256:runtime-digest",
                )
            )

            serialized = output.read_text(encoding="utf-8")
            metadata = json.loads(serialized)
            self.assertEqual(
                metadata["apps_manifest_sha256"],
                hashlib.sha256(manifest_bytes).hexdigest(),
            )
            self.assertNotIn("secret", serialized)
            by_name = {record["name"]: record for record in metadata["applications"]}
            self.assertEqual(by_name["erpnext"]["requested_ref"], "approved-sha")
            self.assertEqual(by_name["erpnext"]["repository"], "github.com/acme/erpnext")
            self.assertEqual(
                metadata["framework_inputs"]["frappe_repository"],
                "github.com/frappe/frappe",
            )

    def test_overlay_updates_rundinova_digest_and_preserves_upstream_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bench_dir = root / "bench"
            create_app(bench_dir, "frappe", "16.1.1")
            create_app(bench_dir, "erpnext", "16.1.1")
            rundinova_dir = create_app(bench_dir, "rundinova_tech", "0.2.1")
            (rundinova_dir / "business_rules.py").write_text(
                "LIMIT = 125\n", encoding="utf-8"
            )
            output = root / "release-metadata.json"
            output.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "release_type": "framework-base",
                        "apps_manifest_sha256": "manifest-digest",
                        "framework_inputs": {"frappe_ref": "approved-framework"},
                        "applications": [
                            {
                                "name": "frappe",
                                "version": "16.1.0",
                                "revision": "frappe-revision",
                                "requested_ref": "approved-framework",
                            },
                            {
                                "name": "erpnext",
                                "version": "16.1.0",
                                "revision": "erpnext-revision",
                                "requested_ref": "approved-erpnext",
                            },
                            {"name": "hrms", "version": "16.1.0"},
                            {"name": "rundinova_tech", "version": "0.2.0"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            METADATA.capture_overlay(
                SimpleNamespace(
                    bench_dir=bench_dir,
                    output=output,
                    base_image="rundinova/erpnext:approved-base",
                    base_image_id="sha256:approved-image-id",
                )
            )

            metadata = json.loads(output.read_text(encoding="utf-8"))
            by_name = {record["name"]: record for record in metadata["applications"]}
            self.assertEqual(metadata["release_type"], "rundinova-overlay")
            self.assertEqual(metadata["base_image"], "rundinova/erpnext:approved-base")
            self.assertEqual(metadata["base_image_id"], "sha256:approved-image-id")
            self.assertEqual(metadata["apps_manifest_sha256"], "manifest-digest")
            self.assertEqual(by_name["frappe"]["revision"], "frappe-revision")
            self.assertEqual(by_name["erpnext"]["requested_ref"], "approved-erpnext")
            self.assertEqual(by_name["erpnext"]["version"], "16.1.1")
            self.assertEqual(by_name["rundinova_tech"]["version"], "0.2.1")
            self.assertEqual(
                by_name["rundinova_tech"]["source_sha256"],
                METADATA.source_digest(rundinova_dir),
            )
            self.assertFalse(metadata["upstream_revisions_available"])


if __name__ == "__main__":
    unittest.main()
