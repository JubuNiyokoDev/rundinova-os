"""Keep the standalone business core independent from runtime adapters."""

import ast
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORTS = {
    "frappe",
    "httpx",
    "psycopg",
    "psycopg2",
    "pymysql",
    "requests",
    "socket",
    "sqlite3",
    "sqlalchemy",
    "urllib.request",
    "urllib3",
}


class TestFrameworkBoundary(unittest.TestCase):
    def test_business_core_does_not_import_framework_or_io_adapters(self):
        violations = []
        for path in CORE_ROOT.rglob("*.py"):
            if "tests" in path.relative_to(CORE_ROOT).parts:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = [node.module]
                else:
                    continue

                for module in imported:
                    if any(
                        module == forbidden or module.startswith(f"{forbidden}.")
                        for forbidden in FORBIDDEN_IMPORTS
                    ):
                        violations.append(
                            f"{path.relative_to(CORE_ROOT)}:{node.lineno}: {module}"
                        )

        self.assertEqual(
            [], violations, "Core must use ports, not framework or I/O adapters"
        )


if __name__ == "__main__":
    unittest.main()
