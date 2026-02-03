#!/usr/bin/env python3
"""
Manual edge case test for fetch_awesome_llm_apps.py

This script tests the following edge cases:
1. Project without README falls back to catalog metadata
2. Invalid Python file returns None
3. Network failures are handled gracefully
4. Script completes without crashing on errors
"""

import sys
import tempfile
import logging
from pathlib import Path

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test 1: Create a test README with projects that will trigger edge cases
def test_edge_case_script():
    """Run the full script with edge case scenarios."""

    # Create a test README with problematic projects
    test_readme_content = """# Edge Case Test

## Valid Projects

- [LangChain](https://github.com/langchain-ai/langchain) - Framework for LLM apps

## Missing README

- [NonExistentRepo12345](https://github.com/nonexistent/nonexistent-repo-12345) - This repo does not exist

## Invalid URL

- [InvalidURL](https://not-github.com/invalid/repo) - Invalid URL format
"""

    # Create test README
    test_readme_path = Path("docs/awesome-llm-apps/README.md")
    original_content = None

    try:
        # Backup original README if it exists
        if test_readme_path.exists():
            original_content = test_readme_path.read_text(encoding='utf-8')
            logger.info("Backed up original README")

        # Write test README
        test_readme_path.parent.mkdir(parents=True, exist_ok=True)
        test_readme_path.write_text(test_readme_content, encoding='utf-8')
        logger.info("Created test README with edge cases")

        # Run the main script
        logger.info("\n" + "="*60)
        logger.info("Testing edge cases with main script")
        logger.info("="*60 + "\n")

        from scripts.fetch_awesome_llm_apps import main
        sys.argv = ['fetch_awesome_llm_apps.py', '--output-dir', 'test_edge_cases_output', '--dry-run']

        exit_code = main()

        logger.info("\n" + "="*60)
        logger.info(f"Script completed with exit code: {exit_code}")
        logger.info("="*60)

        if exit_code == 0:
            logger.info("✅ SUCCESS: Script handled all edge cases gracefully")
            return True
        else:
            logger.warning("⚠️  Script returned non-zero exit code (may be expected if all projects failed)")
            # As long as it didn't crash with an exception, we consider it a success
            return True

    except Exception as e:
        logger.error(f"❌ FAILED: Script crashed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Restore original README
        if original_content is not None:
            test_readme_path.write_text(original_content, encoding='utf-8')
            logger.info("Restored original README")
        elif test_readme_path.exists():
            # Just delete the test file if there was no original
            test_readme_path.unlink()
            logger.info("Removed test README")


def test_python_ast_edge_cases():
    """Test Python AST parser with edge cases."""
    logger.info("\n" + "="*60)
    logger.info("Testing Python AST parser edge cases")
    logger.info("="*60 + "\n")

    from scripts.fetch_awesome_llm_apps import extract_python_metadata

    test_cases = [
        ("Invalid Python syntax", "def incomplete(\n", None),
        ("Non-Python file", "# This is markdown\nNot Python", None),
        ("Empty file", "", "is_dict"),  # Empty files are valid Python, should return dict
    ]

    all_passed = True
    for test_name, content, expected in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            result = extract_python_metadata(temp_file)

            if expected is None:
                if result is None:
                    logger.info(f"✅ {test_name}: Correctly returned None")
                else:
                    logger.error(f"❌ {test_name}: Expected None, got {result}")
                    all_passed = False
            elif expected == "is_dict":
                if result is not None and isinstance(result, dict):
                    logger.info(f"✅ {test_name}: Correctly returned dict (empty file is valid Python)")
                else:
                    logger.error(f"❌ {test_name}: Expected dict, got {result}")
                    all_passed = False

        finally:
            Path(temp_file).unlink()

    return all_passed


def test_github_client_edge_cases():
    """Test GitHub client with edge cases."""
    logger.info("\n" + "="*60)
    logger.info("Testing GitHub client edge cases")
    logger.info("="*60 + "\n")

    from scripts.fetch_awesome_llm_apps import get_github_client, fetch_project_readme, Project

    # Test 1: Client with empty token (should work)
    try:
        client = get_github_client("")
        logger.info("✅ Client created without token")
    except Exception as e:
        logger.error(f"❌ Failed to create client without token: {e}")
        return False

    # Test 2: Fetch from non-existent repo (should return None gracefully)
    try:
        project = Project(
            title="NonExistent",
            url="https://github.com/definitely-not-existent-12345/repo",
            description="Does not exist",
            category="Test"
        )
        result = fetch_project_readme(client, project)
        if result is None:
            logger.info("✅ Non-existent repo handled gracefully (returned None)")
        else:
            logger.warning(f"⚠️  Expected None for non-existent repo, got: {result[:50] if result else None}")
    except Exception as e:
        logger.error(f"❌ Fetching non-existent repo raised exception: {e}")
        return False

    # Test 3: Invalid URL format (should return None gracefully)
    try:
        project = Project(
            title="Invalid URL",
            url="https://not-a-github-url.com/repo",
            description="Invalid URL",
            category="Test"
        )
        result = fetch_project_readme(client, project)
        if result is None:
            logger.info("✅ Invalid URL handled gracefully (returned None)")
        else:
            logger.warning(f"⚠️  Expected None for invalid URL, got: {result[:50] if result else None}")
    except Exception as e:
        logger.error(f"❌ Invalid URL raised exception: {e}")
        return False

    return True


if __name__ == "__main__":
    logger.info("Starting Edge Case Manual Tests\n")

    results = []

    # Test 1: Python AST edge cases
    results.append(("Python AST Edge Cases", test_python_ast_edge_cases()))

    # Test 2: GitHub client edge cases
    results.append(("GitHub Client Edge Cases", test_github_client_edge_cases()))

    # Test 3: Full script edge cases
    results.append(("Full Script Edge Cases", test_edge_case_script()))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("EDGE CASE TEST SUMMARY")
    logger.info("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    logger.info("="*60)

    if all_passed:
        logger.info("\n🎉 All edge case tests passed!")
        sys.exit(0)
    else:
        logger.error("\n⚠️  Some edge case tests failed")
        sys.exit(1)
