"""Guard the manual self-hosted image release boundary."""

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).parents[3]
RELEASE_WORKFLOW = (
    REPOSITORY / ".github" / "workflows" / "rundinova-release-candidate.yml"
)
CHECKS_WORKFLOW = REPOSITORY / ".github" / "workflows" / "rundinova-checks.yml"


class TestReleaseWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        cls.checks = CHECKS_WORKFLOW.read_text(encoding="utf-8")

    def test_manual_release_is_limited_to_main(self):
        self.assertIn("workflow_dispatch:", self.release)
        self.assertIn('"refs/heads/main"', self.release)
        self.assertNotIn("on:\n  push:", self.release)

    def test_candidate_build_requires_checks_and_pinned_ghcr_base(self):
        self.assertIn("workflow_call:", self.checks)
        self.assertIn("uses: ./.github/workflows/rundinova-checks.yml", self.release)
        self.assertLess(
            self.release.index("needs: checks"), self.release.index("docker push")
        )
        self.assertIn("@sha256:[a-f0-9]{64}", self.release)

    def test_candidate_has_narrow_registry_write_access_and_immutable_tags(self):
        self.assertIn("packages: write", self.release)
        self.assertIn("Refusing to overwrite existing image tag", self.release)
        self.assertIn('"$RELEASE_TAG" == latest', self.release)

    def test_private_base_failure_does_not_assume_package_access_is_the_cause(
        self,
    ):
        self.assertIn("Pinned base pull failed", self.release)
        self.assertIn("package access, digest validity, and runner image-store depth", self.release)

    def test_candidate_uses_containerd_image_store_for_deep_base_images(self):
        self.assertIn("docker/setup-docker-action@v5", self.release)
        self.assertIn('"containerd-snapshotter": true', self.release)
        self.assertIn("io.containerd.snapshotter.v1", self.release)

    def test_candidate_never_deploys_or_changes_production(self):
        self.assertIn("images/rundinova/Overlay.Containerfile", self.release)
        self.assertIn("Smoke-check image assets and release metadata", self.release)
        self.assertIn("Production was not changed.", self.release)
        self.assertNotIn("docker compose", self.release)
        self.assertNotIn("CUSTOM_TAG", self.release)


if __name__ == "__main__":
    unittest.main()
