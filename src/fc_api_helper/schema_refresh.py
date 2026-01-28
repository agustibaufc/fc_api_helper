"""OpenAPI schema fetching and caching utilities."""

import json
import os
import sys
import subprocess
import requests
from fc_api_helper.colors import Colors, success, error, info


def fetch_openapi_schema(schema_url, cache_file, base_url=None):
    """Fetch OpenAPI schema from URL and save to cache.

    Args:
        schema_url: URL to fetch the schema from
        cache_file: Path to save the cached schema
        base_url: Base URL of the API (for error messages)
    """
    cache_dir = os.path.dirname(cache_file)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

    print(info(f"Fetching schema from {schema_url}..."), file=sys.stderr)

    try:
        response = requests.get(schema_url, timeout=30)
        response.raise_for_status()
        schema = response.text
    except requests.exceptions.RequestException as e:
        print(error(f"Error: Failed to fetch schema from {schema_url}"), file=sys.stderr)
        if base_url:
            print(info(f"Is the server reachable at {base_url}?"), file=sys.stderr)
        print(info(f"Error details: {e}"), file=sys.stderr)
        sys.exit(1)

    if not schema:
        print(error(f"Error: Empty response from {schema_url}"), file=sys.stderr)
        sys.exit(1)

    try:
        schema_json = json.loads(schema)
    except json.JSONDecodeError:
        print(error(f"Error: Invalid JSON response from {schema_url}"), file=sys.stderr)
        sys.exit(1)

    with open(cache_file, 'w') as f:
        f.write(schema)

    endpoint_count = len(schema_json.get('paths', {}))

    print(success(f"✓ Fetched schema from {schema_url}"), file=sys.stderr)
    print(success(f"✓ Saved complete schema to {cache_file}"), file=sys.stderr)
    print(success(f"✓ Schema contains {endpoint_count} endpoints"), file=sys.stderr)


def refresh_be_schema():
    """Refresh BE API schema."""
    cache_dir = os.path.expanduser("~/.cache/api-schemas")
    fetch_openapi_schema(
        "http://localhost:8080/api/schema.json",
        os.path.join(cache_dir, "be-api.json"),
        "http://localhost:8080"
    )


def refresh_dpl_schema():
    """Refresh DPL API schema."""
    cache_dir = os.path.expanduser("~/.cache/api-schemas")
    fetch_openapi_schema(
        "http://localhost:8030/openapi.json",
        os.path.join(cache_dir, "dpl-api.json"),
        "http://localhost:8030"
    )
