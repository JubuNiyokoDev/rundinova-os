"""Guard the self-hosted environment example against stale image releases."""

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[3]


def env_values(path):
	values = {}
	for raw_line in path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if line and not line.startswith("#") and "=" in line:
			key, value = line.split("=", 1)
			values[key] = value
	return values


class TestDeploymentTemplate(unittest.TestCase):
	def test_environment_example_requires_an_explicit_available_release(self):
		values = env_values(ROOT / "rundinova.env.example")

		self.assertEqual(values["ERPNEXT_VERSION"], "v16.37.7")
		self.assertEqual(values["CUSTOM_IMAGE"], "rundinova/erpnext")
		self.assertIn("replace", values["CUSTOM_TAG"].lower())
		self.assertEqual(values["PULL_POLICY"], "never")
		self.assertNotIn("16.37.7-rn.25-navigation-assets", values["CUSTOM_TAG"])

	def test_first_deploy_instructions_explain_image_availability(self):
		readme = (ROOT / "docs/rundinova/README.md").read_text(encoding="utf-8")

		self.assertIn("make that image available on the Docker host", readme)
		self.assertIn("`PULL_POLICY=never`", readme)
		self.assertIn("docker image inspect", readme)


if __name__ == "__main__":
	unittest.main()
