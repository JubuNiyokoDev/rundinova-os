"""Focused provider contract checks for the repository review service."""

import json
import os
import unittest
from unittest.mock import Mock, patch

import requests
from rundinova_tech.ai_review import review_repository


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

        self.assertEqual(response["executive_summary"], "ok")
        self.assertEqual(response["scan"]["provider"], "cohere")
        self.assertEqual(response["scan"]["model"], "command-r7b-12-2024")
        self.assertEqual(response["web_sources"], [])
        self.assertEqual(post.call_args.args[0], "https://api.cohere.com/v2/chat")
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key"
        )
        self.assertEqual(
            post.call_args.kwargs["json"]["response_format"], {"type": "json_object"}
        )

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
