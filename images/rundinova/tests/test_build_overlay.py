"""Exercise the app-only builder without changing the local Docker daemon."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).parents[3]
BUILDER = REPOSITORY / "images" / "rundinova" / "build-overlay.sh"
BASE_IMAGE = "rundinova/erpnext:approved-base"
BASE_IMAGE_ID = "sha256:approved-base-id"


class TestBuildOverlay(unittest.TestCase):
    def test_overlay_replaces_the_prior_app_tree_instead_of_leaving_stale_files(self):
        containerfile = (REPOSITORY / "images" / "rundinova" / "Overlay.Containerfile").read_text(
            encoding="utf-8"
        )

        copy_source = "COPY --chown=frappe:frappe apps/rundinova_tech /tmp/rundinova_tech-source"
        remove_old_tree = "rm -rf apps/rundinova_tech"
        install_new_tree = "mv /tmp/rundinova_tech-source apps/rundinova_tech"

        self.assertIn(copy_source, containerfile)
        self.assertIn(remove_old_tree, containerfile)
        self.assertIn(install_new_tree, containerfile)
        self.assertLess(containerfile.index(copy_source), containerfile.index(remove_old_tree))
        self.assertLess(containerfile.index(remove_old_tree), containerfile.index(install_new_tree))

    def test_builder_passes_resolved_base_id_and_never_pulls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            state_file = root / "built"
            args_file = root / "build-args.json"
            fake_docker = binary_dir / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "args = sys.argv[1:]\n"
                "state = os.environ['FAKE_DOCKER_STATE']\n"
                "if args[:2] == ['image', 'inspect']:\n"
                "    reference = args[-1]\n"
                "    if reference == 'rundinova/erpnext:approved-base':\n"
                "        print('sha256:approved-base-id') if '--format' in args else None\n"
                "        sys.exit(0)\n"
                "    if reference == 'rundinova/erpnext:16.37.7-rn.test':\n"
                "        if os.path.exists(state):\n"
                "            print('sha256:candidate-id') if '--format' in args else None\n"
                "            sys.exit(0)\n"
                "        sys.exit(1)\n"
                "    sys.exit(1)\n"
                "if args and args[0] == 'build':\n"
                "    with open(os.environ['FAKE_DOCKER_ARGS'], 'w') as f:\n"
                "        json.dump(args, f)\n"
                "    open(state, 'w').close()\n"
                "    sys.exit(0)\n"
                "sys.exit(2)\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{binary_dir}{os.pathsep}{env['PATH']}"
            env["FAKE_DOCKER_STATE"] = str(state_file)
            env["FAKE_DOCKER_ARGS"] = str(args_file)
            result = subprocess.run(
                ["bash", str(BUILDER), BASE_IMAGE, "16.37.7-rn.test"],
                cwd=REPOSITORY,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            build_args = json.loads(args_file.read_text(encoding="utf-8"))
            self.assertIn("--pull=false", build_args)
            self.assertIn(f"--build-arg=RUNDINOVA_BASE_IMAGE={BASE_IMAGE}", build_args)
            self.assertIn(
                f"--build-arg=RUNDINOVA_BASE_IMAGE_ID={BASE_IMAGE_ID}", build_args
            )
            self.assertIn("sha256:candidate-id", result.stdout)


if __name__ == "__main__":
    unittest.main()
