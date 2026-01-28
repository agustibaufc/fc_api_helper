"""Curl wrapper utilities for API requests."""

import os
import sys
import subprocess
import re
import json
from fc_api_helper.auth import authenticate_be


# Environment configurations
ENV_CONFIG = {
    'local': {
        'be': {
            'api_key_file': '/tmp/api-key-local',
            'base_url': 'http://localhost:8080'
        },
        'dpl': {
            'api_key': 'dev-api-key',
            'base_url': 'http://localhost:8030'
        }
    },
    'test': {
        'be': {
            'api_key_file': '/tmp/api-key-test',
            'base_url': 'https://api.test.fundcraft.lu'
        },
        'dpl': {
            'api_key': 'test-api-key',
            'base_url': 'https://test-dpl-url.example.com'
        }
    }
}


def format_json_output(output):
    """Format JSON output with indentation.

    Args:
        output: String that may contain JSON

    Returns:
        Formatted JSON string, or original string if not valid JSON
    """
    try:
        parsed = json.loads(output)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        return output


def filter_auth_headers(args, header_pattern):
    """Filter out authentication headers from curl arguments.

    Args:
        args: List of curl arguments
        header_pattern: Regex pattern to match headers to filter

    Returns:
        List of filtered arguments
    """
    filtered_args = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ('-H', '--header'):
            if i + 1 < len(args):
                next_arg = args[i + 1]
                if re.match(header_pattern, next_arg, re.IGNORECASE):
                    i += 2
                    continue

        if re.match(rf'^-H{header_pattern}', arg, re.IGNORECASE) or \
           re.match(rf'^--header={header_pattern}', arg, re.IGNORECASE):
            i += 1
            continue

        filtered_args.append(arg)
        i += 1

    return filtered_args


def run_curl_with_token_auth(environment='local'):
    """Execute curl with Authorization Token header.

    Automatically authenticates if receiving 401 UNAUTHORIZED response.

    Args:
        environment: Environment to use ('local', 'test', 'prod')
    """
    config = ENV_CONFIG[environment]['be']
    api_key_file = config['api_key_file']

    def execute_curl(api_key):
        """Execute curl command with given API key."""
        args = sys.argv[1:]
        # Filter out --env flag from curl args
        filtered_args = [arg for i, arg in enumerate(args)
                        if not (arg == '--env' or (i > 0 and args[i-1] == '--env'))]
        filtered_args = filter_auth_headers(filtered_args, r'^[Aa]uthorization:.*')

        curl_cmd = [
            'curl',
            '-s',
            '-w', '\n__HTTP_STATUS__:%{http_code}',
            '-H', f'Authorization: Token {api_key}',
            '-H', 'Content-Type: application/json'
        ] + filtered_args

        try:
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            return result
        except FileNotFoundError:
            print("Error: curl not found", file=sys.stderr)
            sys.exit(1)

    api_key = None
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()

    if not api_key:
        print("No valid API key found. Starting authentication...", file=sys.stderr)
        authenticate_be(api_key_file=api_key_file, environment=environment)
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()

    result = execute_curl(api_key)

    status_code = None
    output = result.stdout
    if '__HTTP_STATUS__:' in output:
        parts = output.rsplit('__HTTP_STATUS__:', 1)
        output = parts[0]
        status_code = parts[1].strip() if len(parts) > 1 else None

    if status_code == '401':
        print("Received 401 UNAUTHORIZED. Re-authenticating...", file=sys.stderr)
        authenticate_be(api_key_file=api_key_file, environment=environment)
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()

        result = execute_curl(api_key)

        output = result.stdout
        if '__HTTP_STATUS__:' in output:
            parts = output.rsplit('__HTTP_STATUS__:', 1)
            output = parts[0]

    if output:
        print(format_json_output(output))

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(result.returncode)


def run_curl_with_api_key(environment='local'):
    """Execute curl with X-API-KEY header.

    Args:
        environment: Environment to use ('local', 'test', 'prod')
    """
    config = ENV_CONFIG[environment]['dpl']
    api_key = config['api_key']

    args = sys.argv[1:]
    # Filter out --env flag from curl args
    filtered_args = [arg for i, arg in enumerate(args)
                    if not (arg == '--env' or (i > 0 and args[i-1] == '--env'))]
    filtered_args = filter_auth_headers(filtered_args, r'^[Xx]-[Aa][Pp][Ii]-[Kk][Ee][Yy]:.*')

    curl_cmd = [
        'curl',
        '-s',
        '-H', f'X-API-KEY: {api_key}',
        '-H', 'Content-Type: application/json'
    ] + filtered_args

    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)

        if result.stdout:
            print(format_json_output(result.stdout))

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: curl not found", file=sys.stderr)
        sys.exit(1)
