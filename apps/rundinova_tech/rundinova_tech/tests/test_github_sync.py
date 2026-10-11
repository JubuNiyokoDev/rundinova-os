"""Unit tests for the read-only GitHub sync module."""

import os
import unittest
from unittest.mock import MagicMock, patch

from rundinova_tech.github_sync import (
    parse_github_url,
    fetch_repository_info,
    fetch_recent_commits,
    sync_repository,
)


class TestParseGithubUrl(unittest.TestCase):
    def test_valid_url(self):
        self.assertEqual(
            parse_github_url("https://github.com/org/repo"), ("org", "repo")
        )

    def test_valid_url_trailing_slash(self):
        self.assertEqual(
            parse_github_url("https://github.com/org/repo/"), ("org", "repo")
        )

    def test_valid_url_with_dots(self):
        self.assertEqual(
            parse_github_url("https://github.com/my-org/my.repo"), ("my-org", "my.repo")
        )

    def test_invalid_url_no_path(self):
        self.assertIsNone(parse_github_url("https://github.com"))

    def test_invalid_url_gitlab(self):
        self.assertIsNone(parse_github_url("https://gitlab.com/org/repo"))

    def test_invalid_url_empty(self):
        self.assertIsNone(parse_github_url(""))

    def test_invalid_url_none(self):
        self.assertIsNone(parse_github_url(None))

    def test_invalid_url_ssh(self):
        self.assertIsNone(parse_github_url("git@github.com:org/repo.git"))


class TestFetchRepositoryInfo(unittest.TestCase):
    @patch("rundinova_tech.github_sync.requests.get")
    def test_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "org/repo",
            "description": "Test repo",
            "default_branch": "main",
            "open_issues_count": 5,
            "watchers_count": 10,
            "stargazers_count": 42,
            "forks_count": 3,
            "language": "Python",
            "pushed_at": "2026-09-30T10:00:00Z",
            "html_url": "https://github.com/org/repo",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_repository_info("org", "repo")
        self.assertEqual(result["open_issues_count"], 5)
        self.assertEqual(result["stargazers_count"], 42)
        self.assertEqual(result["language"], "Python")
        self.assertEqual(result["full_name"], "org/repo")
        mock_get.assert_called_once()

    @patch("rundinova_tech.github_sync.requests.get")
    def test_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            fetch_repository_info("org", "nonexistent")


class TestFetchRecentCommits(unittest.TestCase):
    @patch("rundinova_tech.github_sync.requests.get")
    def test_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "sha": "abc1234567890",
                "commit": {
                    "message": "Fix bug\nMore details",
                    "author": {"name": "Dev", "date": "2026-09-29T08:00:00Z"},
                },
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_recent_commits("org", "repo", limit=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sha"], "abc12345")
        self.assertEqual(result[0]["message"], "Fix bug")
        self.assertEqual(result[0]["author"], "Dev")


class TestSyncRepository(unittest.TestCase):
    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            sync_repository("not-a-url")

    @patch("rundinova_tech.github_sync.fetch_recent_commits")
    @patch("rundinova_tech.github_sync.fetch_repository_info")
    def test_success(self, mock_info, mock_commits):
        mock_info.return_value = {
            "full_name": "org/repo",
            "description": "A project",
            "default_branch": "main",
            "open_issues_count": 2,
            "watchers_count": 8,
            "stargazers_count": 10,
            "forks_count": 1,
            "language": "JavaScript",
            "pushed_at": "2026-09-28T12:00:00Z",
            "html_url": "https://github.com/org/repo",
        }
        mock_commits.return_value = [
            {"sha": "abc", "message": "init", "author": "Dev", "date": ""}
        ]

        result = sync_repository("https://github.com/org/repo")
        self.assertEqual(result["owner"], "org")
        self.assertEqual(result["repo"], "repo")
        self.assertEqual(result["stargazers_count"], 10)
        self.assertIn("recent_commits", result)


class TestGitHubToken(unittest.TestCase):
    @patch("rundinova_tech.github_sync.requests.get")
    @patch.dict(os.environ, {"RUNDINOVA_GITHUB_TOKEN": "fine-grained-test-token"})
    def test_token_is_used_for_private_repository_read_requests(self, mock_get):
        response = MagicMock()
        response.json.side_effect = [
            {
                "full_name": "RundiNova/PartenerWanje",
                "default_branch": "main",
            },
            [],
        ]
        response.raise_for_status = MagicMock()
        mock_get.return_value = response

        result = sync_repository("https://github.com/RundiNova/PartenerWanje")

        self.assertEqual(result["full_name"], "RundiNova/PartenerWanje")
        self.assertEqual(mock_get.call_count, 2)
        for request in mock_get.call_args_list:
            headers = request.kwargs["headers"]
            self.assertEqual(headers["Authorization"], "Bearer fine-grained-test-token")
            self.assertEqual(headers["X-GitHub-Api-Version"], "2026-03-10")
        self.assertNotIn("Authorization", result)

    @patch("rundinova_tech.github_sync.requests.get")
    @patch.dict(os.environ, {"RUNDINOVA_GITHUB_TOKEN": ""})
    def test_public_repository_requests_work_without_a_token(self, mock_get):
        response = MagicMock()
        response.json.side_effect = [{"full_name": "org/repo"}, []]
        response.raise_for_status = MagicMock()
        mock_get.return_value = response

        sync_repository("https://github.com/org/repo")

        for request in mock_get.call_args_list:
            self.assertNotIn("Authorization", request.kwargs["headers"])


if __name__ == "__main__":
    unittest.main()
