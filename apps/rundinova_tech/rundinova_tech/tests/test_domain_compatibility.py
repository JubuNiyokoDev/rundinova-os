import unittest

from rundinova_core.food import calculate_food_budget_usage
from rundinova_tech.rundinova_tech.domain.food import calculate_food_budget_usage as legacy_food_usage


class TestDomainCompatibility(unittest.TestCase):
	def test_previous_domain_import_path_reexports_core_implementation(self):
		self.assertIs(legacy_food_usage, calculate_food_budget_usage)


if __name__ == "__main__":
	unittest.main()
