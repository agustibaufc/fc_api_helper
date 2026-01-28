"""Authentication utilities."""

import sys
import getpass
import requests


# Import ENV_CONFIG to avoid duplication
def get_auth_url(environment):
    """Get authentication URL for environment."""
    from fc_api_helper.curl_wrapper import ENV_CONFIG
    base_url = ENV_CONFIG[environment]['be']['base_url']
    return f"{base_url}/api/api-token-auth/"


def authenticate_be(api_key_file, environment='local'):
    """Authenticate with BE API and save token.

    Args:
        api_key_file: Path to save the API key
        environment: Environment to use ('local', 'test', 'prod')
    """
    username = getpass.getuser()
    email = f"{username}@fundcraft.lu"

    auth_url = get_auth_url(environment)

    print(f"Authenticating as: {email} (environment: {environment})", file=sys.stderr)
    password = getpass.getpass("Password: ")

    if not password:
        print("Error: Password cannot be empty", file=sys.stderr)
        sys.exit(1)

    try:
        response = requests.post(
            auth_url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"Error: Authentication failed (HTTP {response.status_code})", file=sys.stderr)
            print(response.text, file=sys.stderr)
            sys.exit(1)

        data = response.json()
        token = data.get('token')

        if not token:
            print("Error: Could not extract token from response", file=sys.stderr)
            sys.exit(1)

        with open(api_key_file, 'w') as f:
            f.write(token)

        print("✓ Authentication successful", file=sys.stderr)
        print(f"✓ API key saved to {api_key_file}", file=sys.stderr)

    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
