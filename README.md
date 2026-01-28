# FC API Helper

API automation tools for BE and DPL services.

## Installation
from this folder:

```bash
pip install -e .
```

Or with uv:

```bash
uv pip install -e .
```
Add this to your .zshrc
```bash
# Wrapper for be-api to inject command into prompt
be-api() {
    local command_output=$(command be-api "$@")
    local exit_code=$?

    if [ $exit_code -eq 0 ] && [ -n "$command_output" ]; then
        print -z "$command_output"
    fi
}

# Wrapper for dpl-api to inject command into prompt
dpl-api() {
    local command_output=$(command dpl-api "$@")
    local exit_code=$?

    if [ $exit_code -eq 0 ] && [ -n "$command_output" ]; then
        print -z "$command_output"
    fi
}

```

## Commands

### BE (Backend) Commands

- `be-curl` - Curl wrapper with automatic Token authentication (auto-authenticates on 401)
- `be-api` - Interactive API explorer with fzf (auto-fetches schema if missing)

### DPL Commands

- `dpl-curl` - Curl wrapper with X-API-KEY authentication
- `dpl-api` - Interactive API explorer with fzf (auto-fetches schema if missing)

## Usage

### Authentication (BE only)

Authentication is handled automatically when you use `be-curl` or `be-api`. If no valid token exists or a 401 UNAUTHORIZED response is received, you will be prompted to authenticate.

### Exploring APIs

```bash
be-api   # Opens interactive API explorer
dpl-api  # Opens interactive API explorer
```

### Direct curl requests

```bash
be-curl http://localhost:8080/api/endpoint/
dpl-curl http://localhost:8030/api/endpoint/
```

## Requirements

- Python 3.8+
- curl
- fzf (for interactive API explorer)
