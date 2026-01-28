"""DPL API explorer CLI entry point."""

import os
import sys
import argparse
from fc_api_helper.api_explorer import run_api_explorer
from fc_api_helper.schema_refresh import fetch_openapi_schema


# Environment configurations for DPL API
ENV_CONFIG = {
    'local': {
        'base_url': 'http://localhost:8030',
        'schemas': [
            {
                'cache_file': os.path.expanduser('~/.cache/api-schemas/dpl-api-local.json'),
                'schema_url': 'http://localhost:8030/openapi.json',
                'path_prefix': '',
            },
        ],
    },
    'test': {
        'base_url': 'http://dpl.test.private.fundcraft.lu',
        'schemas': [
            {
                'cache_file': os.path.expanduser('~/.cache/api-schemas/dpl-api-test.json'),
                'schema_url': 'http://dpl.test.private.fundcraft.lu/openapi.json',
                'path_prefix': '',
            },
        ],
    },
}


def main():
    """Run DPL API explorer."""
    parser = argparse.ArgumentParser(description='DPL API explorer')
    parser.add_argument('--refresh', action='store_true',
                       help='Refresh schema cache before running')
    parser.add_argument('--env', choices=['local', 'test'], default='local',
                       help='Environment to use (default: local)')
    args = parser.parse_args()

    env_config = ENV_CONFIG[args.env]
    config = {
        'schemas': env_config['schemas'],
        'base_url': env_config['base_url'],
        'curl_command': 'dpl-curl',
        'environment': args.env
    }

    if args.refresh:
        print(f"Refreshing schema for environment: {args.env}", file=sys.stderr)
        for schema_config in config['schemas']:
            fetch_openapi_schema(
                schema_config['schema_url'],
                schema_config['cache_file'],
                config['base_url']
            )
        print("", file=sys.stderr)

    run_api_explorer(config)


if __name__ == '__main__':
    main()
