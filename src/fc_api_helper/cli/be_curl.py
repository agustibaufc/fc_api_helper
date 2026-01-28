"""BE curl wrapper CLI entry point."""

import argparse
from fc_api_helper.curl_wrapper import run_curl_with_token_auth


def main():
    """Execute curl with BE API authentication."""
    parser = argparse.ArgumentParser(description='BE curl wrapper with authentication')
    parser.add_argument('--env', choices=['local', 'test'], default='local',
                       help='Environment to use (default: local)')
    args, _ = parser.parse_known_args()

    run_curl_with_token_auth(environment=args.env)


if __name__ == '__main__':
    main()
