"""Focused provider contract checks for the repository review service."""

import json
import os
import unittest
from unittest.mock import Mock, patch

import requests
from rundinova_core.application.repository_review import INSUFFICIENT_EVIDENCE_SUMMARY
from rundinova_tech.ai_review import render_markdown, review_repository


class TestAIReview(unittest.TestCase):
    def setUp(self):
        self.repository = {
            "full_name": "RundiNova/example",
            "description": "Example repo",
            "language": "Python",
            "default_branch": "main",
            "open_issues_count": 0,
            "pushed_at": "2026-10-01T00:00:00Z",
        }
        self.source = {
            "branch": "main",
            "tree_files": 3,
            "candidate_files": 2,
            "files_read": 2,
            "truncated": False,
        }

    @patch.dict(
        os.environ,
        {
            "RUNDINOVA_AI_PROVIDER": "cohere",
            "COHERE_API_KEY": "test-key",
            "COHERE_MODEL": "command-r7b-12-2024",
        },
        clear=True,
    )
    @patch("rundinova_tech.ai_review.requests.post")
    def test_cohere_json_response_is_parsed_without_web_claims(self, post):
        post.return_value.json.return_value = {
            "message": {
                "content": [
                    {"type": "text", "text": json.dumps({"executive_summary": "ok"})}
                ]
            }
        }
        response = review_repository(self.repository, self.source, [])

        self.assertEqual(response["executive_summary"], INSUFFICIENT_EVIDENCE_SUMMARY)
        self.assertEqual(response["scan"]["provider"], "cohere")
        self.assertEqual(response["scan"]["model"], "command-r7b-12-2024")
        self.assertEqual(response["web_sources"], [])
        self.assertEqual(response["analysis_quality"], "insufficient_evidence")
        self.assertIsNone(response["readiness_score"])
        self.assertEqual(response["sales_verdict"], "À évaluer — preuves insuffisantes")
        self.assertEqual(response["market_research_status"], "not_performed")
        self.assertIn(
            "ne pas traiter les affirmations de marché comme des faits",
            response["market_opportunity"].lower(),
        )
        self.assertEqual(post.call_args.args[0], "https://api.cohere.com/v2/chat")
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key"
        )
        self.assertEqual(
            post.call_args.kwargs["json"]["response_format"], {"type": "json_object"}
        )

    @patch.dict(
        os.environ,
        {
            "RUNDINOVA_AI_PROVIDER": "cohere",
            "COHERE_API_KEY": "test-key",
        },
        clear=True,
    )
    @patch("rundinova_tech.ai_review.requests.post")
    def test_repository_claims_require_exact_excerpts_from_scanned_files(self, post):
        excerpts = [
            "The project exposes a documented health endpoint.",
            "The service stores all records in PostgreSQL.",
            "Automated tests cover the billing workflow.",
        ]
        self.source["files"] = [
            {"path": "README.md", "content": f"Overview\n{excerpts[0]}\n{excerpts[1]}"},
            {"path": "tests/billing.py", "content": excerpts[2]},
        ]
        post.return_value.json.return_value = {
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "executive_summary": "Le dépôt décrit un health endpoint.",
                                "evidence": [
                                    {
                                        "claim": "Le README décrit le health endpoint.",
                                        "source_path": "README.md",
                                        "excerpt": excerpts[0],
                                    },
                                    {
                                        "claim": "La persistance utilise PostgreSQL.",
                                        "source_path": "README.md",
                                        "excerpt": excerpts[1],
                                    },
                                    {
                                        "claim": "Le workflow de facturation est testé.",
                                        "source_path": "tests/billing.py",
                                        "excerpt": excerpts[2],
                                    },
                                    {
                                        "claim": "L'équipe est expérimentée.",
                                        "source_path": "not-scanned.md",
                                        "excerpt": "The team has shipped many mature products.",
                                    },
                                ],
                                "market_opportunity": "Marché en croissance.",
                            }
                        ),
                    }
                ]
            }
        }

        report = review_repository(self.repository, self.source, [])
        markdown = render_markdown(report)

        self.assertEqual(report["analysis_quality"], "evidence_linked")
        self.assertEqual(len(report["evidence"]), 3)
        self.assertEqual(report["evidence"][0]["source_path"], "README.md")
        self.assertEqual(
            report["executive_summary"], "Le dépôt décrit un health endpoint."
        )
        self.assertIn(
            "Qualité des preuves :** preuves liées à des extraits du dépôt", markdown
        )
        self.assertIn("Étude de marché :** non effectuée", markdown)
        self.assertIn(
            "Aucune recherche Web externe vérifiable", report["market_opportunity"]
        )

    @patch.dict(
        os.environ,
        {"RUNDINOVA_AI_PROVIDER": "cohere", "COHERE_API_KEY": "test-key"},
        clear=True,
    )
    @patch("rundinova_tech.ai_review.requests.post")
    def test_nonmatching_excerpts_invalidate_executive_summary(self, post):
        self.source["files"] = [
            {"path": "README.md", "content": "Actual project content here."}
        ]
        post.return_value.json.return_value = {
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "executive_summary": "Le projet est mature et prêt à vendre.",
                                "evidence": [
                                    {
                                        "claim": "Le produit est prêt à vendre.",
                                        "source_path": "README.md",
                                        "excerpt": "The team has shipped many mature products.",
                                    }
                                ],
                            }
                        ),
                    }
                ]
            }
        }

        report = review_repository(self.repository, self.source, [])

        self.assertEqual(report["analysis_quality"], "insufficient_evidence")
        self.assertEqual(report["executive_summary"], INSUFFICIENT_EVIDENCE_SUMMARY)
        self.assertIsNone(report["readiness_score"])
        self.assertEqual(report["sales_verdict"], "À évaluer — preuves insuffisantes")
        self.assertEqual(report["completed_capabilities"], [])
        self.assertIn("non évaluée — preuves insuffisantes", render_markdown(report))

    @patch.dict(
        os.environ,
        {"RUNDINOVA_AI_PROVIDER": "cohere", "COHERE_API_KEY": "test-key"},
        clear=True,
    )
    @patch("rundinova_tech.ai_review.requests.post")
    def test_provider_error_reports_status_without_disclosing_key(self, post):
        response = Mock(status_code=401)
        post.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )

        with self.assertRaisesRegex(
            RuntimeError, r"Cohere repository analysis failed \(HTTP 401\)"
        ) as error:
            review_repository(self.repository, self.source, [])

        self.assertNotIn("test-key", str(error.exception))


if __name__ == "__main__":
    unittest.main()
