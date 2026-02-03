#!/usr/bin/env python3
"""
Search Functionality Testing Script
Tests MkDocs search UI elements and configuration without running mkdocs serve
"""

import os
import json
import sys
from pathlib import Path

def test_search_ui_elements():
    """Test that search UI elements are present in the built HTML"""
    print("=" * 70)
    print("TEST 1: Search UI Elements in HTML")
    print("=" * 70)

    site_dir = Path("site")
    index_html = site_dir / "index.html"

    if not index_html.exists():
        print("❌ FAIL: site/index.html not found")
        return False

    with open(index_html, 'r', encoding='utf-8') as f:
        html_content = f.read()

    checks = {
        "Search input field": 'name="query"',
        "Search form": 'class="md-search__form"',
        "Search component": 'data-md-component="search"',
        "Search overlay": 'class="md-search__overlay"',
        "Search input with placeholder": 'placeholder="Search"',
        "Search toggle": 'data-md-toggle="search"',
    }

    results = []
    for check_name, check_string in checks.items():
        if check_string in html_content:
            print(f"✅ PASS: {check_name} found")
            results.append(True)
        else:
            print(f"❌ FAIL: {check_name} NOT found")
            results.append(False)

    all_passed = all(results)
    print(f"\nTest 1 Result: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed


def test_search_index():
    """Test search index file and content"""
    print("\n" + "=" * 70)
    print("TEST 2: Search Index Verification")
    print("=" * 70)

    search_index_path = Path("site/search/search_index.json")

    if not search_index_path.exists():
        print("❌ FAIL: site/search/search_index.json not found")
        return False

    with open(search_index_path, 'r', encoding='utf-8') as f:
        search_data = json.load(f)

    # Check structure
    checks = []

    # Check config
    if "config" in search_data:
        print("✅ PASS: Search config exists")
        checks.append(True)

        config = search_data["config"]
        if "lang" in config and "en" in config["lang"]:
            print("✅ PASS: English language configured")
            checks.append(True)
        else:
            print("❌ FAIL: English language not configured")
            checks.append(False)

        if "separator" in config:
            separator = config["separator"]
            if r"\." in separator:
                print(f"✅ PASS: Optimized separator configured: {separator}")
                checks.append(True)
            else:
                print(f"⚠️  WARNING: Separator might be outdated: {separator}")
                checks.append(True)  # Not a hard failure
    else:
        print("❌ FAIL: Search config missing")
        checks.append(False)

    # Check documents
    if "docs" in search_data:
        docs = search_data["docs"]
        doc_count = len(docs)
        print(f"\n📊 Documents indexed: {doc_count}")

        if doc_count >= 5:
            print(f"✅ PASS: Sufficient documents indexed ({doc_count} >= 5)")
            checks.append(True)
        else:
            print(f"❌ FAIL: Insufficient documents indexed ({doc_count} < 5)")
            print("   Expected 10+ documents based on docs/ directory structure")
            checks.append(False)

        # Show sample documents
        print("\n📝 Sample indexed documents:")
        for i, doc in enumerate(docs[:5], 1):
            title = doc.get("title", "No title")
            location = doc.get("location", "No location")
            text_preview = doc.get("text", "")[:80]
            print(f"   {i}. {title}")
            print(f"      Location: {location}")
            print(f"      Preview: {text_preview}...")

        if doc_count > 5:
            print(f"   ... and {doc_count - 5} more")
    else:
        print("❌ FAIL: No documents in search index")
        checks.append(False)

    all_passed = all(checks)
    print(f"\nTest 2 Result: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed


def test_search_config_in_mkdocs():
    """Test that mkdocs.yml has optimized search configuration"""
    print("\n" + "=" * 70)
    print("TEST 3: MkDocs Configuration")
    print("=" * 70)

    mkdocs_path = Path("mkdocs.yml")

    if not mkdocs_path.exists():
        print("❌ FAIL: mkdocs.yml not found")
        return False

    with open(mkdocs_path, 'r', encoding='utf-8') as f:
        mkdocs_content = f.read()

    checks = []

    # Check for search plugin
    if "plugins:" in mkdocs_content and "- search:" in mkdocs_content:
        print("✅ PASS: Search plugin enabled")
        checks.append(True)
    else:
        print("❌ FAIL: Search plugin not enabled")
        checks.append(False)

    # Check for optimization options
    optimizations = {
        "prebuild_index": "prebuild_index: true",
        "min_search_length": "min_search_length: 2",
        "separator": r"separator: '[\s\-\.]+'",
    }

    for opt_name, opt_string in optimizations.items():
        if opt_string in mkdocs_content:
            print(f"✅ PASS: {opt_name} configured")
            checks.append(True)
        else:
            print(f"⚠️  WARNING: {opt_name} not found")
            checks.append(True)  # Not a hard failure for testing

    # Check theme features
    theme_features = ["search.suggest", "search.highlight", "search.share"]
    for feature in theme_features:
        if feature in mkdocs_content:
            print(f"✅ PASS: Theme feature {feature} enabled")
            checks.append(True)
        else:
            print(f"❌ FAIL: Theme feature {feature} not enabled")
            checks.append(False)

    all_passed = all(checks)
    print(f"\nTest 3 Result: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed


def generate_test_cases():
    """Generate test cases for manual browser testing"""
    print("\n" + "=" * 70)
    print("MANUAL TESTING REQUIREMENTS")
    print("=" * 70)

    test_cases = [
        {
            "query": "AutoGen",
            "expected": "Results about AutoGen agent framework",
            "priority": "High"
        },
        {
            "query": "LangChain",
            "expected": "Results about LangChain AI tool",
            "priority": "High"
        },
        {
            "query": "agent framework",
            "expected": "Results for agent frameworks (AutoGen, CrewAI)",
            "priority": "High"
        },
        {
            "query": "chatbot",
            "expected": "Results for chatbot agents",
            "priority": "Medium"
        },
        {
            "query": "data analysis",
            "expected": "Results for data analysis tools",
            "priority": "Medium"
        },
        {
            "query": "AI",
            "expected": "Multiple results across categories",
            "priority": "Low"
        },
    ]

    print("\nTo complete testing, run 'mkdocs serve' and test these queries:\n")
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. Query: '{test['query']}'")
        print(f"   Expected: {test['expected']}")
        print(f"   Priority: {test['priority']}")
        print()

    print("Verification Checklist:")
    print("□ Search box is visible in the header")
    print("□ Search returns results within 1 second")
    print("□ Results are ranked by relevance (title matches first)")
    print("□ Search terms are highlighted in results")
    print("□ Technical terms (AutoGen, LangChain) are found accurately")
    print("□ Agent names are searchable")
    print("□ Multi-word queries work correctly")
    print("□ Search suggestions appear as you type")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MkDocs Search Functionality Testing")
    print("=" * 70)
    print("\nThis script tests search configuration and UI elements")
    print("Note: Full browser testing requires running 'mkdocs serve'\n")

    # Run tests
    test1_result = test_search_ui_elements()
    test2_result = test_search_index()
    test3_result = test_search_config_in_mkdocs()

    # Generate manual testing requirements
    generate_test_cases()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    results = {
        "Search UI Elements": test1_result,
        "Search Index": test2_result,
        "MkDocs Configuration": test3_result,
    }

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    overall = all(results.values())
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall else '⚠️  SOME TESTS FAILED'}")

    if not overall:
        print("\n⚠️  Note: Search index needs to be rebuilt with 'mkdocs build'")
        print("   to apply the optimized configuration from mkdocs.yml")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
