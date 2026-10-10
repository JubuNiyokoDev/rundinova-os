import unittest

from rundinova_core.application.food_progress_link import ensure_food_progress_link


class FakeFoodProgressLinkPort:
	def __init__(self, existing=None):
		self.existing = existing
		self.calls = []

	def find_progress(self, budget, item):
		self.calls.append(("find", budget, item))
		return self.existing

	def create_progress(self, budget, item):
		self.calls.append(("create", budget, item))
		return "progress-new"


class TestFoodProgressLinkUseCase(unittest.TestCase):
	def test_keeps_explicit_progress_without_persistence_calls(self):
		port = FakeFoodProgressLinkPort()

		result = ensure_food_progress_link("budget-1", "rice", "progress-1", port)

		self.assertEqual(result, "progress-1")
		self.assertEqual(port.calls, [])

	def test_incomplete_expense_does_not_query_or_create(self):
		for budget, item in ((None, "rice"), ("budget-1", None)):
			with self.subTest(budget=budget, item=item):
				port = FakeFoodProgressLinkPort()
				self.assertIsNone(ensure_food_progress_link(budget, item, None, port))
				self.assertEqual(port.calls, [])

	def test_reuses_existing_progress(self):
		port = FakeFoodProgressLinkPort(existing="progress-1")

		result = ensure_food_progress_link("budget-1", "rice", None, port)

		self.assertEqual(result, "progress-1")
		self.assertEqual(port.calls, [("find", "budget-1", "rice")])

	def test_creates_progress_only_after_lookup_misses(self):
		port = FakeFoodProgressLinkPort()

		result = ensure_food_progress_link("budget-1", "rice", None, port)

		self.assertEqual(result, "progress-new")
		self.assertEqual(
			port.calls,
			[("find", "budget-1", "rice"), ("create", "budget-1", "rice")],
		)


if __name__ == "__main__":
	unittest.main()
