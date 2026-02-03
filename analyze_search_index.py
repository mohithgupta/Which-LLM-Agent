#!/usr/bin/env python3
"""Analyze search index content in detail."""
import json

try:
    with open('site/search/search_index.json', 'r') as f:
        data = json.load(f)

    print("=" * 60)
    print("SEARCH INDEX ANALYSIS")
    print("=" * 60)

    print(f"\n📊 Total Documents Indexed: {len(data['docs'])}")
    print(f"\n⚙️  Search Configuration:")
    print(f"   - Language: {data['config'].get('lang', 'N/A')}")
    print(f"   - Separator: {data['config'].get('separator', 'N/A')}")
    print(f"   - Pipeline: {data['config'].get('pipeline', 'N/A')}")
    print(f"   - Fields: {list(data['config'].get('fields', {}).keys())}")

    print(f"\n📄 Indexed Documents:")
    for i, doc in enumerate(data['docs'], 1):
        print(f"\n   {i}. {doc.get('title', 'Untitled')}")
        print(f"      Location: {doc.get('location', 'Unknown')}")
        text_preview = doc.get('text', '')[:100]
        print(f"      Text preview: {text_preview}...")

    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)

    # Verification checks
    docs_count = len(data['docs'])
    config = data['config']

    # Check 1: Document count
    if docs_count > 5:
        print("\n✅ PASS: More than 5 documents indexed")
    else:
        print(f"\n❌ FAIL: Only {docs_count} documents indexed (expected >5)")
        print("   This indicates the search index is incomplete or outdated.")

    # Check 2: Configuration
    expected_separator = r'[\s\-\.]+'
    actual_separator = config.get('separator', '')

    if actual_separator == expected_separator:
        print("✅ PASS: Search configuration is up to date")
    else:
        print(f"⚠️  WARNING: Search configuration appears outdated")
        print(f"   Expected: {expected_separator}")
        print(f"   Actual: {actual_separator}")
        print("   The site may need to be rebuilt with: mkdocs build")

    print("\n" + "=" * 60)

except FileNotFoundError:
    print('❌ ERROR: search_index.json not found at site/search/search_index.json')
    print('The documentation site needs to be built first.')
except Exception as e:
    print(f'❌ ERROR: {e}')
