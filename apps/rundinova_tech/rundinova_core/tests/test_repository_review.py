import unittest

from rundinova_core.application.repository_review import (
    INSUFFICIENT_EVIDENCE_SUMMARY,
    INSUFFICIENT_MARKET_RESEARCH,
    prepare_repository_review,
)


class TestRepositoryReview(unittest.TestCase):
    def setUp(self):
        self.context = {
            "files": [
                {
                    "path": "README.md",
                    "content": (
                        "The project exposes a documented health endpoint.\n"
                        "The service stores all records in PostgreSQL."
                    ),
                },
                {
                    "path": "tests/billing.py",
                    "content": "Automated tests cover the billing workflow.",
                },
            ]
        }
        self.report = {
            "executive_summary": "The project has a health endpoint.",
            "readiness_score": 72,
            "sales_verdict": "Promising",
            "completed_capabilities": ["Health endpoint"],
            "evidence": [
                {
                    "claim": "A documented health endpoint exists.",
                    "source_path": "README.md",
                    "excerpt": "The project exposes a documented health endpoint.",
                },
                {
                    "claim": "PostgreSQL is used for persistence.",
                    "source_path": "README.md",
                    "excerpt": "The service stores all records in PostgreSQL.",
                },
                {
                    "claim": "Billing has automated tests.",
                    "source_path": "tests/billing.py",
                    "excerpt": "Automated tests cover the billing workflow.",
                },
            ],
            "market_opportunity": "Potential market claim",
        }

    def test_keeps_exact_evidence_and_does_not_mutate_input(self):
        original = dict(self.report)

        result = prepare_repository_review(self.report, self.context, [])

        self.assertEqual(result["analysis_quality"], "evidence_linked")
        self.assertEqual(len(result["evidence"]), 3)
        self.assertEqual(result["readiness_score"], 72)
        self.assertEqual(result["market_research_status"], "not_performed")
        self.assertEqual(result["market_opportunity"], INSUFFICIENT_MARKET_RESEARCH)
        self.assertEqual(self.report, original)

    def test_rejects_unscanned_or_nonmatching_excerpts_and_suppresses_verdict(self):
        report = dict(self.report)
        report["evidence"] = [
            {
                "claim": "The team is experienced.",
                "source_path": "not-scanned.md",
                "excerpt": "The team shipped many mature products.",
            }
        ]

        result = prepare_repository_review(report, self.context, [])

        self.assertEqual(result["analysis_quality"], "insufficient_evidence")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["executive_summary"], INSUFFICIENT_EVIDENCE_SUMMARY)
        self.assertIsNone(result["readiness_score"])
        self.assertEqual(result["sales_verdict"], "À évaluer — preuves insuffisantes")
        self.assertEqual(result["completed_capabilities"], [])

    def test_preserves_market_analysis_only_when_grounding_sources_exist(self):
        sources = [{"title": "Market source", "url": "https://example.com/report"}]

        result = prepare_repository_review(self.report, self.context, sources)

        self.assertEqual(result["market_research_status"], "grounded_sources_available")
        self.assertEqual(result["web_sources"], sources)
        self.assertEqual(result["market_opportunity"], "Potential market claim")


if __name__ == "__main__":
    unittest.main()
