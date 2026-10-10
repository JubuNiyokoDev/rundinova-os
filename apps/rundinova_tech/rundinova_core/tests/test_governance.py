"""Framework-independent rules for RundiNova governance records."""

import unittest
from datetime import date

from rundinova_core.governance import (
    asset_validation_actions,
    decision_validation_actions,
    document_validation_actions,
    goal_achievement,
    goal_validation_actions,
)


class TestGovernanceDomain(unittest.TestCase):
    def test_restricted_document_requires_owner_and_valid_review_date(self):
        self.assertEqual(
            document_validation_actions(
                date(2026, 1, 1), date(2026, 1, 2), "Restricted", None
            ),
            ("review_before_document_date", "restricted_document_requires_owner"),
        )

    def test_completed_decision_requires_evidence_or_follow_up(self):
        self.assertEqual(
            decision_validation_actions("Completed", None, None, None, None),
            ("completed_decision_requires_follow_up",),
        )
        self.assertEqual(
            decision_validation_actions("Completed", "TASK-1", None, None, None),
            (),
        )

    def test_follow_up_date_cannot_precede_decision(self):
        self.assertEqual(
            decision_validation_actions(
                "Open", None, None, date(2026, 1, 1), date(2026, 1, 2)
            ),
            ("follow_up_before_decision_date",),
        )

    def test_asset_value_and_assignment_rules(self):
        self.assertEqual(
            asset_validation_actions(-1, 0, "In Use", None, None),
            ("asset_value_negative", "asset_in_use_requires_assignment_or_location"),
        )
        self.assertEqual(
            asset_validation_actions(0, 0, "In Use", "Employee-1", None), ()
        )

    def test_goal_period_error_precedes_target_error(self):
        self.assertEqual(
            goal_validation_actions(date(2026, 2, 1), date(2026, 1, 1), 0),
            ("goal_period_invalid",),
        )
        self.assertEqual(
            goal_validation_actions(date(2026, 1, 1), date(2026, 2, 1), 0),
            ("goal_target_not_positive",),
        )

    def test_goal_progress_is_bounded_and_only_completes_at_target(self):
        self.assertEqual(goal_achievement(5, 10), (50.0, None))
        self.assertEqual(goal_achievement(-1, 10), (0, None))
        self.assertEqual(goal_achievement(15, 10), (100, "Achieved"))


if __name__ == "__main__":
    unittest.main()
