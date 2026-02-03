#!/usr/bin/env python3
"""Verify search index content and configuration."""
import json

try:
    with open('site/search/search_index.json', 'r') as f:
        data = json.load(f)

    num_docs = len(data['docs'])
    config = data['config']

    print(f'Docs indexed: {num_docs}')
    print(f'Config: {config}')

    # Check if configuration is expected
    if num_docs < 5:
        print(f'\n⚠️  WARNING: Only {num_docs} documents indexed.')
        print('Expected: More than 5 documents for full documentation site.')
        print('This may indicate the search index is incomplete or outdated.')

    # Check for optimized configuration
    expected_separator = r'[\s\-\.]+'
    actual_separator = config.get('separator', '')

    if actual_separator != expected_separator:
        print(f'\n⚠️  WARNING: Search configuration may be outdated.')
        print(f'Expected separator: {expected_separator}')
        print(f'Actual separator: {actual_separator}')
        print('The site may need to be rebuilt to apply new configuration.')
    else:
        print('\n✅ Search configuration is up to date.')

except FileNotFoundError:
    print('❌ ERROR: search_index.json not found at site/search/search_index.json')
    print('The documentation site needs to be built first.')
except Exception as e:
    print(f'❌ ERROR: {e}')
