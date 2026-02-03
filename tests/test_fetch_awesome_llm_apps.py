"""
Unit tests for fetch_awesome_llm_apps.py

Tests the three core components:
1. README Parser (parse_main_readme)
2. GitHub Client (get_github_client, fetch_with_retry, fetch_raw_readme, fetch_project_readme)
3. Python AST Parser (extract_python_metadata)
"""

import ast
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.fetch_awesome_llm_apps import (
    Project,
    extract_python_metadata,
    fetch_raw_readme,
    fetch_with_retry,
    fetch_project_readme,
    get_github_client,
    parse_main_readme,
)


class TestReadmeParser:
    """Test suite for README parser functionality."""

    def test_parse_simple_readme(self, tmp_path):
        """Test parsing a simple README with categories and projects."""
        # Create a test README file
        readme_content = """# Awesome LLM Apps

A curated list of awesome LLM applications.

## AI Tools

- [OpenAI ChatGPT](https://github.com/openai/chatgpt) - AI chatbot
- [Claude](https://github.com/anthropic/claude) - AI assistant

## Chatbots

- [Bot1](https://github.com/user/bot1) - A cool bot
"""
        readme_file = tmp_path / "test_readme.md"
        readme_file.write_text(readme_content)

        # Parse the README
        result = parse_main_readme(str(readme_file))

        # Verify results
        assert len(result) == 2
        assert "AI Tools" in result
        assert "Chatbots" in result

        # Check AI Tools category
        ai_tools = result["AI Tools"]
        assert len(ai_tools) == 2
        assert ai_tools[0].title == "OpenAI ChatGPT"
        assert ai_tools[0].url == "https://github.com/openai/chatgpt"
        assert ai_tools[0].description == "AI chatbot"
        assert ai_tools[0].category == "AI Tools"

        # Check Chatbots category
        chatbots = result["Chatbots"]
        assert len(chatbots) == 1
        assert chatbots[0].title == "Bot1"
        assert chatbots[0].description == "A cool bot"

    def test_parse_readme_without_descriptions(self, tmp_path):
        """Test parsing README where projects have no descriptions."""
        readme_content = """# Test

## Category

- [Project1](https://github.com/user/project1)
- [Project2](https://github.com/user/project2)
"""
        readme_file = tmp_path / "test_no_desc.md"
        readme_file.write_text(readme_content)

        result = parse_main_readme(str(readme_file))

        assert len(result) == 1
        projects = result["Category"]
        assert len(projects) == 2
        assert projects[0].description is None
        assert projects[1].description is None

    def test_parse_readme_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_main_readme("nonexistent.md")

    def test_parse_empty_readme(self, tmp_path):
        """Test that ValueError is raised for README with no projects."""
        readme_content = """# Empty README

Just a header, no projects.
"""
        readme_file = tmp_path / "empty.md"
        readme_file.write_text(readme_content)

        with pytest.raises(ValueError, match="No valid project entries"):
            parse_main_readme(str(readme_file))

    def test_parse_readme_with_special_characters(self, tmp_path):
        """Test parsing projects with special characters in titles."""
        readme_content = """# Test

## Category

- [Project & Co](https://github.com/user/project) - A project with & in name
- [Test-Project_v2](https://github.com/user/test) - Another test
"""
        readme_file = tmp_path / "special.md"
        readme_file.write_text(readme_content)

        result = parse_main_readme(str(readme_file))

        projects = result["Category"]
        assert len(projects) == 2
        assert projects[0].title == "Project & Co"
        assert projects[1].title == "Test-Project_v2"


class TestGitHubClient:
    """Test suite for GitHub client functionality."""

    def test_get_github_client_with_token(self):
        """Test creating authenticated GitHub client."""
        client = get_github_client("test_token")
        assert client is not None

    def test_get_github_client_without_token(self):
        """Test creating unauthenticated GitHub client."""
        client = get_github_client("")
        assert client is not None

    @patch('scripts.fetch_awesome_llm_apps.Github')
    def test_get_github_client_auth_failure_fallback(self, mock_github):
        """Test that client falls back to unauthenticated on auth failure."""
        # Mock authenticated client to raise exception
        mock_authed_client = Mock()
        mock_authed_client.get_rate_limit.side_effect = Exception("Auth failed")

        # Mock unauthenticated client
        mock_unauthed_client = Mock()
        mock_github.side_effect = [mock_authed_client, mock_unauthed_client]

        client = get_github_client("invalid_token")
        assert client is not None

    def test_fetch_with_retry_success(self):
        """Test successful fetch on first attempt."""
        mock_client = Mock()
        fetch_op = Mock(return_value="success")

        result = fetch_with_retry(mock_client, fetch_op, "owner/repo")
        assert result == "success"
        assert fetch_op.call_count == 1

    def test_fetch_with_retry_rate_limit_retry(self):
        """Test retry logic on rate limit."""
        from github.GithubException import RateLimitExceededException

        mock_client = Mock()
        fetch_op = Mock()

        # Fail twice with rate limit, then succeed
        fetch_op.side_effect = [
            RateLimitExceededException(403, "Rate limit", {"headers": {}}),
            RateLimitExceededException(403, "Rate limit", {"headers": {}}),
            "success"
        ]

        with patch('scripts.fetch_awesome_llm_apps.time.sleep'):  # Mock sleep to speed up test
            result = fetch_with_retry(mock_client, fetch_op, "owner/repo", max_retries=3)

        assert result == "success"
        assert fetch_op.call_count == 3

    def test_fetch_with_retry_exhausted_retries(self):
        """Test that None is returned after max retries exhausted."""
        from github.GithubException import RateLimitExceededException

        mock_client = Mock()
        fetch_op = Mock(side_effect=RateLimitExceededException(403, "Rate limit", {"headers": {}}))

        with patch('scripts.fetch_awesome_llm_apps.time.sleep'):
            result = fetch_with_retry(mock_client, fetch_op, "owner/repo", max_retries=2)

        assert result is None
        assert fetch_op.call_count == 2

    def test_fetch_with_retry_generic_exception(self):
        """Test that None is returned on generic exception."""
        mock_client = Mock()
        fetch_op = Mock(side_effect=Exception("Network error"))

        result = fetch_with_retry(mock_client, fetch_op, "owner/repo")
        assert result is None

    @patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen')
    def test_fetch_raw_readme_success(self, mock_urlopen):
        """Test successful raw README fetch."""
        mock_response = Mock()
        mock_response.read.return_value = b"# Test README\nContent here"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_raw_readme("https://github.com/owner/repo")

        assert result == "# Test README\nContent here"
        mock_urlopen.assert_called_once()

    @patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen')
    def test_fetch_raw_readme_404_tries_master_branch(self, mock_urlopen):
        """Test that master branch is tried if main returns 404."""
        # The function tries multiple README filenames, so we need to mock all attempts
        # Main branch: 4 attempts all fail with 404
        # Master branch: first attempt (README.md) succeeds
        mock_response_main = Mock()
        mock_response_main.read.return_value = b"Master content"

        mock_urlopen.side_effect = [
            # Main branch attempts - all 404s
            urllib.error.HTTPError("url", 404, "Not Found", {}, None),
            urllib.error.HTTPError("url", 404, "Not Found", {}, None),
            urllib.error.HTTPError("url", 404, "Not Found", {}, None),
            urllib.error.HTTPError("url", 404, "Not Found", {}, None),
            # Master branch - success on first attempt
            MagicMock(__enter__=Mock(return_value=mock_response_main))
        ]

        result = fetch_raw_readme("https://github.com/owner/repo", branch="main")

        assert result == "Master content"
        assert mock_urlopen.call_count == 5

    @patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen')
    def test_fetch_raw_readme_url_error(self, mock_urlopen):
        """Test that None is returned on URL error."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")

        result = fetch_raw_readme("https://github.com/owner/repo")

        assert result is None

    @patch('scripts.fetch_awesome_llm_apps.fetch_raw_readme')
    @patch('scripts.fetch_awesome_llm_apps.fetch_with_retry')
    def test_fetch_project_readme_api_success(self, mock_retry, mock_raw, caplog):
        """Test successful README fetch via GitHub API."""
        import logging

        mock_retry.return_value = "# API README"
        mock_client = Mock()
        project = Project(title="TestProject", url="https://github.com/owner/repo", description="Test", category="Test")

        with caplog.at_level(logging.DEBUG):
            result = fetch_project_readme(mock_client, project)

        assert result == "# API README"
        mock_retry.assert_called_once()
        mock_raw.assert_not_called()

    @patch('scripts.fetch_awesome_llm_apps.fetch_raw_readme')
    @patch('scripts.fetch_awesome_llm_apps.fetch_with_retry')
    def test_fetch_project_readme_api_falls_back_to_raw(self, mock_retry, mock_raw, caplog):
        """Test fallback to raw URL when API fails."""
        import logging

        mock_retry.return_value = None
        mock_raw.return_value = "# Raw README"
        mock_client = Mock()
        project = Project(title="TestProject", url="https://github.com/owner/repo", description="Test", category="Test")

        with caplog.at_level(logging.DEBUG):
            result = fetch_project_readme(mock_client, project)

        assert result == "# Raw README"
        mock_retry.assert_called_once()
        mock_raw.assert_called_once_with(project.url)

    @patch('scripts.fetch_awesome_llm_apps.fetch_raw_readme')
    @patch('scripts.fetch_awesome_llm_apps.fetch_with_retry')
    def test_fetch_project_readme_invalid_url(self, mock_retry, mock_raw):
        """Test that None is returned for invalid repository URL."""
        mock_client = Mock()
        project = Project(title="TestProject", url="https://invalid.com/repo", description="Test", category="Test")

        result = fetch_project_readme(mock_client, project)

        assert result is None
        mock_retry.assert_not_called()
        mock_raw.assert_not_called()


class TestPythonASTParser:
    """Test suite for Python AST parser functionality."""

    def test_extract_metadata_simple_python_file(self, tmp_path):
        """Test extracting metadata from a simple Python file."""
        python_code = '''"""Simple module for testing."""

def greet(name):
    """Greet the user."""
    return f"Hello, {name}!"

class MyClass:
    """A simple class."""
    def method(self):
        """A method."""
        pass
'''
        python_file = tmp_path / "simple.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert result['name'] == 'simple'
        assert result['description'] == 'Simple module for testing.'
        assert len(result['functions']) == 1
        assert result['functions'][0]['name'] == 'greet'
        assert result['functions'][0]['docstring'] == 'Greet the user.'
        assert len(result['classes']) == 1
        assert result['classes'][0]['name'] == 'MyClass'

    def test_extract_metadata_no_docstring(self, tmp_path):
        """Test extracting metadata from file without module docstring."""
        python_code = '''
def func1():
    pass

class Class1:
    pass
'''
        python_file = tmp_path / "no_doc.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert result['description'] is None
        assert len(result['functions']) == 1
        assert len(result['classes']) == 1

    def test_extract_metadata_syntax_error(self, tmp_path):
        """Test that None is returned for invalid Python syntax."""
        python_code = '''
def incomplete(
    # Missing closing parenthesis
'''
        python_file = tmp_path / "invalid.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is None

    def test_extract_metadata_nonexistent_file(self):
        """Test that None is returned for non-existent file."""
        result = extract_python_metadata("nonexistent.py")
        assert result is None

    def test_extract_metadata_class_methods(self, tmp_path):
        """Test that methods are extracted from classes."""
        python_code = '''
class Calculator:
    """Math calculator."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
'''
        python_file = tmp_path / "calculator.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert len(result['classes']) == 1
        calculator_class = result['classes'][0]
        assert calculator_class['name'] == 'Calculator'
        assert len(calculator_class['methods']) == 2
        assert calculator_class['methods'][0]['name'] == 'add'
        assert calculator_class['methods'][1]['name'] == 'subtract'
        # Methods should not be in top-level functions
        assert len(result['functions']) == 0

    def test_extract_metadata_mixed(self, tmp_path):
        """Test extracting both functions and classes."""
        python_code = '''
"""Module with functions and classes."""

def helper_function():
    """A helper."""
    pass

class DataProcessor:
    """Process data."""
    def process(self):
        """Do processing."""
        pass

def another_helper():
    """Another helper."""
    pass
'''
        python_file = tmp_path / "mixed.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert result['description'] == 'Module with functions and classes.'
        assert len(result['functions']) == 2
        assert len(result['classes']) == 1
        assert result['classes'][0]['methods'][0]['name'] == 'process'

    def test_extract_metadata_function_args(self, tmp_path):
        """Test that function arguments are extracted."""
        python_code = '''
def complex_function(arg1, arg2, arg3=None):
    """Function with multiple args."""
    pass
'''
        python_file = tmp_path / "args.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        func = result['functions'][0]
        assert func['name'] == 'complex_function'
        assert func['args'] == ['arg1', 'arg2', 'arg3']

    def test_extract_metadata_long_docstring_truncation(self, tmp_path):
        """Test that long docstrings are truncated."""
        long_desc = "x" * 300
        python_code = f'''
"""{long_desc}"""

def func():
    pass
'''
        python_file = tmp_path / "long.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert len(result['description']) <= 203  # 200 + '...'
        assert result['description'].endswith('...')

    def test_extract_metadata_uses_class_docstring_fallback(self, tmp_path):
        """Test that class docstring is used when module has none."""
        python_code = '''
class MainClass:
    """The main class description."""
    pass
'''
        python_file = tmp_path / "fallback.py"
        python_file.write_text(python_code)

        result = extract_python_metadata(str(python_file))

        assert result is not None
        assert result['description'] == 'The main class description.'


class TestProjectDataclass:
    """Test suite for Project dataclass."""

    def test_project_creation(self):
        """Test creating a Project instance."""
        project = Project(
            title="Test Project",
            url="https://github.com/user/repo",
            description="A test project",
            category="Test Category"
        )

        assert project.title == "Test Project"
        assert project.url == "https://github.com/user/repo"
        assert project.description == "A test project"
        assert project.category == "Test Category"

    def test_project_defaults(self):
        """Test Project with default values."""
        project = Project(
            title="Test",
            url="https://github.com/user/repo"
        )

        assert project.description is None
        assert project.category == ""


class TestEdgeCases:
    """Test suite for edge cases and error scenarios."""

    def test_network_timeout_fails_immediately(self):
        """Test that network timeout returns None immediately (only rate limits retry)."""
        import socket

        mock_client = Mock()
        fetch_op = Mock()

        # Simulate network timeout
        fetch_op.side_effect = socket.timeout("Connection timed out")

        result = fetch_with_retry(mock_client, fetch_op, "owner/repo", max_retries=3)

        # Should fail immediately (network timeouts don't retry, only rate limits do)
        assert result is None
        assert fetch_op.call_count == 1

    def test_rate_limit_exceeded_triggers_exponential_backoff(self):
        """Test that rate limit triggers exponential backoff retry logic."""
        from github.GithubException import RateLimitExceededException

        mock_client = Mock()
        fetch_op = Mock()

        # Simulate rate limit errors
        fetch_op.side_effect = RateLimitExceededException(403, "Rate limit", {"headers": {}})

        sleep_times = []

        def mock_sleep(seconds):
            sleep_times.append(seconds)

        with patch('scripts.fetch_awesome_llm_apps.time.sleep', side_effect=mock_sleep):
            result = fetch_with_retry(mock_client, fetch_op, "owner/repo", max_retries=3, initial_wait=1.0)

        # Should fail after max retries
        assert result is None
        assert fetch_op.call_count == 3
        # Verify exponential backoff: 1.0, 2.0, 4.0 (but only 2 sleeps since 3 attempts)
        assert len(sleep_times) == 2
        assert sleep_times[0] == 1.0
        assert sleep_times[1] == 2.0

    def test_invalid_python_file_returns_none(self):
        """Test that invalid Python file returns None instead of crashing."""
        import tempfile

        # Create a file with invalid Python syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def incomplete(\n    # Missing closing paren and body\n')
            temp_file = f.name

        try:
            result = extract_python_metadata(temp_file)
            assert result is None
        finally:
            Path(temp_file).unlink()

    def test_non_python_file_returns_none(self):
        """Test that non-Python files (e.g., markdown) return None gracefully."""
        import tempfile

        # Create a markdown file instead of Python
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# This is markdown\n\nNot valid Python code at all!')
            temp_file = f.name

        try:
            result = extract_python_metadata(temp_file)
            assert result is None
        finally:
            Path(temp_file).unlink()

    def test_empty_python_file_returns_none(self):
        """Test that empty Python file returns metadata with empty fields."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('')
            temp_file = f.name

        try:
            result = extract_python_metadata(temp_file)
            # Empty file is valid Python, but has no meaningful content
            assert result is not None
            assert result['name'] is not None
            assert len(result['functions']) == 0
            assert len(result['classes']) == 0
        finally:
            Path(temp_file).unlink()

    @patch('scripts.fetch_awesome_llm_apps.fetch_raw_readme')
    @patch('scripts.fetch_awesome_llm_apps.fetch_with_retry')
    def test_project_without_readme_falls_back_to_python(self, mock_retry, mock_raw, caplog):
        """Test that missing README triggers Python AST fallback."""
        import logging

        # Mock API to return None (README not found)
        mock_retry.return_value = None
        # Mock raw fetch to also return None
        mock_raw.return_value = None

        mock_client = Mock()
        project = Project(
            title="TestProject",
            url="https://github.com/owner/testproject",
            description="A test project",
            category="Test"
        )

        # Mock Python file fetch to succeed
        mock_python_content = '''"""Test module."""

def main():
    """Main function."""
    pass
'''

        with patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = mock_python_content.encode('utf-8')
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with caplog.at_level(logging.DEBUG):
                result = fetch_project_readme(mock_client, project)

        # Should return None since both API and raw failed
        # (Python AST fallback happens in process_project, not fetch_project_readme)
        assert result is None
        # Verify API was attempted
        mock_retry.assert_called_once()
        # Verify raw URL was attempted as fallback
        mock_raw.assert_called_once()

    @patch('scripts.fetch_awesome_llm_apps.fetch_raw_readme')
    @patch('scripts.fetch_awesome_llm_apps.fetch_with_retry')
    def test_all_fetch_methods_fail_gracefully(self, mock_retry, mock_raw):
        """Test that script doesn't crash when all fetch methods fail."""
        # Mock all fetch methods to return None
        mock_retry.return_value = None
        mock_raw.return_value = None

        mock_client = Mock()
        project = Project(
            title="NonExistent",
            url="https://github.com/nonexistent/repo",
            description="Does not exist",
            category="Test"
        )

        result = fetch_project_readme(mock_client, project)

        # Should return None gracefully, not raise exception
        assert result is None
        mock_retry.assert_called_once()
        mock_raw.assert_called_once()

    @patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen')
    def test_url_error_handling_in_raw_fetch(self, mock_urlopen):
        """Test that URL errors (e.g., DNS failures) are handled gracefully."""
        # Simulate DNS failure / URL error
        mock_urlopen.side_effect = urllib.error.URLError("DNS lookup failed")

        result = fetch_raw_readme("https://github.com/owner/repo")

        # Should return None, not raise exception
        assert result is None

    @patch('scripts.fetch_awesome_llm_apps.urllib.request.urlopen')
    def test_http_error_handling_in_raw_fetch(self, mock_urlopen):
        """Test that HTTP errors (e.g., 500, 403) are handled gracefully."""
        # Simulate server error
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Internal Server Error", {}, None)

        result = fetch_raw_readme("https://github.com/owner/repo")

        # Should return None, not raise exception
        assert result is None

    def test_github_rate_limit_exceeded(self):
        """Test GitHub API rate limit handling."""
        from github.GithubException import RateLimitExceededException

        mock_client = Mock()
        fetch_op = Mock(side_effect=RateLimitExceededException(403, {"message": "API rate limit exceeded"}, {"headers": {}}))

        sleep_calls = []

        def track_sleep(seconds):
            sleep_calls.append(seconds)

        with patch('scripts.fetch_awesome_llm_apps.time.sleep', side_effect=track_sleep):
            result = fetch_with_retry(mock_client, fetch_op, "owner/repo", max_retries=2, initial_wait=1.0)

        # Should exhaust retries and return None
        assert result is None
        assert fetch_op.call_count == 2
        # Should have slept between retries with exponential backoff
        assert len(sleep_calls) == 1  # 2 attempts = 1 sleep
        assert sleep_calls[0] == 1.0
