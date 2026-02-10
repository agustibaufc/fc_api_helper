"""Shared OpenAPI API explorer library."""

import json
import subprocess
import sys
from fc_api_helper.schema_refresh import fetch_openapi_schema
from fc_api_helper.colors import (
    Colors,
    colored,
    header,
    success,
    error,
    info,
    label
)

# Global client UUID (set when user provides x-sirius-client-uuid header, used by prompt_for_value)
_current_client_uuid = None


def merge_schemas(schema_entries):
    """Merge multiple OpenAPI schemas into one.

    Args:
        schema_entries: List of dicts with 'schema' and 'path_prefix' keys

    Returns:
        Merged schema with combined paths and components
    """
    if not schema_entries:
        return {}

    merged = {
        'openapi': schema_entries[0]['schema'].get('openapi', '3.0.0'),
        'info': schema_entries[0]['schema'].get('info', {}),
        'paths': {},
        'components': {
            'schemas': {}
        }
    }

    for entry in schema_entries:
        schema = entry['schema']
        prefix = entry.get('path_prefix', '')

        # Merge paths with prefix
        for path, methods in schema.get('paths', {}).items():
            full_path = f"{prefix}{path}" if prefix else path
            if full_path in merged['paths']:
                merged['paths'][full_path].update(methods)
            else:
                merged['paths'][full_path] = methods

        # Merge component schemas
        components = schema.get('components', {})
        component_schemas = components.get('schemas', {})
        merged['components']['schemas'].update(component_schemas)

    return merged


def load_schema(cache_file, schema_url, base_url):
    """Load the OpenAPI schema from cache file.

    Args:
        cache_file: Path to the schema cache file
        schema_url: URL to fetch the schema from if not cached
        base_url: Base URL of the API (for error messages)
    """
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(info("Schema cache not found at ") + cache_file, file=sys.stderr)
        print(info(f"Fetching schema from {schema_url}..."), file=sys.stderr)
        print("", file=sys.stderr)

        fetch_openapi_schema(schema_url, cache_file, base_url)

        print("", file=sys.stderr)
        print(success("✓ Schema fetched successfully. Continuing..."), file=sys.stderr)
        print("", file=sys.stderr)

        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(error(f"Error: Failed to load schema after refresh: {e}"), file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError:
        print(error(f"Error: Invalid JSON in {cache_file}"), file=sys.stderr)
        sys.exit(1)


def format_endpoints(schema):
    """Format endpoints for fzf selection."""
    endpoints = []
    for path, methods in schema.get('paths', {}).items():
        for method, details in methods.items():
            summary = details.get('summary') or details.get('description') or "No description"
            summary = summary.split('\n')[0].strip()
            if len(summary) > 100:
                summary = summary[:97] + "..."
            endpoints.append(f"{method.upper()} {path} -- {summary}")
    return "\n".join(endpoints)


def select_endpoint_with_fzf(endpoints_text):
    """Use fzf to select an endpoint."""
    try:
        result = subprocess.run(
            ['fzf', '--height=60%', '--reverse', '--border', '--prompt=Select API endpoint: '],
            input=endpoints_text,
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            print(info("No selection made"), file=sys.stderr)
            sys.exit(0)
        return result.stdout.strip()
    except FileNotFoundError:
        print(error("Error: fzf not found"), file=sys.stderr)
        sys.exit(1)


def prompt_for_value(name, required, param_type, description, param_in=''):
    """Prompt user for a parameter value."""
    print("", file=sys.stderr)

    if param_in == 'path':
        print(f"  {label('Variable:')} {{{colored(name, Colors.BRIGHT_MAGENTA)}}}", file=sys.stderr)
    elif param_in == 'query':
        print(f"  {label('Query param:')} ?{colored(name, Colors.BRIGHT_MAGENTA)}=", file=sys.stderr)
    elif param_in == 'header':
        print(f"  {label('Header:')} {colored(name, Colors.BRIGHT_MAGENTA)}", file=sys.stderr)
    elif param_in == 'body':
        print(f"  {label('Body field:')} \"{colored(name, Colors.BRIGHT_MAGENTA)}\"", file=sys.stderr)
    else:
        print(f"  {label('Variable:')} {colored(name, Colors.BRIGHT_MAGENTA)}", file=sys.stderr)

    meta = []
    if required:
        meta.append(colored("REQUIRED", Colors.BRIGHT_RED))
    else:
        meta.append(colored("optional", Colors.YELLOW))
    if param_type:
        meta.append(colored(param_type, Colors.CYAN))

    print(f"  {label('Type:')} {', '.join(meta)}", file=sys.stderr)

    if description:
        print(f"  {label('Description:')} {description}", file=sys.stderr)

    if 'uuid' in name.lower() or (description and 'uuid' in description.lower()):
        try:
            cmd = ['fc-uuid']
            if _current_client_uuid:
                cmd.extend(['--client', _current_client_uuid])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            uuid_value = result.stdout.strip()
            print(f"  {success('✓ Selected:')} {uuid_value}", file=sys.stderr)
            return uuid_value
        except subprocess.CalledProcessError:
            print(f"  {info('fc-uuid failed, falling back to manual input')}", file=sys.stderr)
            print(f"  {label('Enter value:')} ", end='', file=sys.stderr, flush=True)
            return input()
        except FileNotFoundError:
            print(f"  {info('fc-uuid not found, falling back to manual input')}", file=sys.stderr)
            print(f"  {label('Enter value:')} ", end='', file=sys.stderr, flush=True)
            return input()
    else:
        print(f"  {label('Enter value:')} ", end='', file=sys.stderr, flush=True)
        return input()


def get_parameters(schema, path, method, param_in):
    """Get parameters of a specific type (path, query) from the schema."""
    endpoint = schema['paths'].get(path, {}).get(method.lower(), {})
    parameters = endpoint.get('parameters', [])
    return [p for p in parameters if p.get('in') == param_in]


def resolve_ref(schema, ref_path):
    """Resolve a $ref reference in the schema."""
    if not ref_path.startswith('#/'):
        return None

    parts = ref_path[2:].split('/')

    current = schema
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def get_request_body_schema(schema, path, method):
    """Get request body schema from the endpoint."""
    endpoint = schema['paths'].get(path, {}).get(method.lower(), {})
    request_body = endpoint.get('requestBody', {})
    content = request_body.get('content', {})
    json_content = content.get('application/json', {})
    body_schema = json_content.get('schema')

    if body_schema and '$ref' in body_schema:
        ref_path = body_schema['$ref']
        resolved = resolve_ref(schema, ref_path)
        if resolved:
            return resolved

    return body_schema


def generate_example_body(body_schema, full_schema=None):
    """Generate an example JSON body from schema."""
    if 'example' in body_schema:
        return body_schema['example']

    if 'properties' not in body_schema:
        return {}

    properties = body_schema.get('properties', {})
    required_fields = body_schema.get('required', [])
    example = {}

    for prop_name, prop_schema in properties.items():
        if '$ref' in prop_schema and full_schema:
            ref_path = prop_schema['$ref']
            resolved = resolve_ref(full_schema, ref_path)
            if resolved:
                prop_schema = resolved

        if 'example' in prop_schema:
            example[prop_name] = prop_schema['example']
        else:
            prop_type = prop_schema.get('type', 'string')
            description = prop_schema.get('description', '')

            if prop_type == 'string':
                example[prop_name] = f"<{prop_name}>"
            elif prop_type == 'integer':
                example[prop_name] = 0
            elif prop_type == 'number':
                example[prop_name] = 0.0
            elif prop_type == 'boolean':
                example[prop_name] = False
            elif prop_type == 'array':
                example[prop_name] = []
            elif prop_type == 'object':
                example[prop_name] = {}
            else:
                example[prop_name] = None

    return example


def generate_body_with_comments(body_schema, full_schema=None, method='', path=''):
    """Generate JSON body with field descriptions as comments."""
    if not body_schema or 'properties' not in body_schema:
        return json.dumps({}, indent=2)

    properties = body_schema.get('properties', {})
    required_fields = body_schema.get('required', [])

    lines = []
    if method and path:
        lines.append(f"// Endpoint: {method.upper()} {path}")
        lines.append("//")

    lines.append("{")

    prop_items = list(properties.items())
    for idx, (prop_name, prop_schema) in enumerate(prop_items):
        if '$ref' in prop_schema and full_schema:
            ref_path = prop_schema['$ref']
            resolved = resolve_ref(full_schema, ref_path)
            if resolved:
                prop_schema = resolved

        description = prop_schema.get('description', '')
        prop_type = prop_schema.get('type', 'string')
        is_required = prop_name in required_fields

        if 'example' in prop_schema:
            example_value = prop_schema['example']
        else:
            if prop_type == 'string':
                example_value = f"<{prop_name}>"
            elif prop_type == 'integer':
                example_value = 0
            elif prop_type == 'number':
                example_value = 0.0
            elif prop_type == 'boolean':
                example_value = False
            elif prop_type == 'array':
                example_value = []
            elif prop_type == 'object':
                example_value = {}
            else:
                example_value = None

        comment_parts = []
        if description:
            comment_parts.append(description)

        type_info = f"Type: {prop_type}"
        if is_required:
            type_info += " (REQUIRED)"
        comment_parts.append(type_info)

        if comment_parts:
            lines.append(f"  // {' | '.join(comment_parts)}")

        if prop_type == 'array' and 'items' in prop_schema:
            items_schema = prop_schema['items']
            if '$ref' in items_schema and full_schema:
                ref_path = items_schema['$ref']
                resolved = resolve_ref(full_schema, ref_path)
                if resolved:
                    items_schema = resolved

            example_item = generate_example_body(items_schema, full_schema)
            example_json = json.dumps(example_item, indent=2)
            for line in example_json.split('\n'):
                lines.append(f"  // {line}")

        is_last = (idx == len(prop_items) - 1)
        comma = "" if is_last else ","
        lines.append(f'  "{prop_name}": {json.dumps(example_value)}{comma}')

        if not is_last:
            lines.append("")

    lines.append("}")

    return "\n".join(lines)


def strip_json_comments(text):
    """Strip // comments from JSON text."""
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('//'):
            continue

        comment_pos = line.find('//')
        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        if line.strip():
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def prompt_for_body_fields(body_schema, full_schema=None, method='', path=''):
    """Interactively prompt for each field in the request body."""
    if not body_schema:
        return None

    print(header("Request Body"), file=sys.stderr)
    print("", file=sys.stderr)

    if 'properties' not in body_schema:
        print(info("No properties defined in body schema"), file=sys.stderr)
        return None

    properties = body_schema.get('properties', {})
    required_fields = body_schema.get('required', [])

    body = {}

    for prop_name, prop_schema in properties.items():
        # Resolve $ref if present
        if '$ref' in prop_schema and full_schema:
            ref_path = prop_schema['$ref']
            resolved = resolve_ref(full_schema, ref_path)
            if resolved:
                prop_schema = resolved

        prop_type = prop_schema.get('type', 'string')
        description = prop_schema.get('description', '')
        is_required = prop_name in required_fields
        enum_values = prop_schema.get('enum')

        # Handle enum fields with fzf selection
        if enum_values:
            value = prompt_for_enum_value(prop_name, is_required, prop_type, description, enum_values)
        # Handle nested objects recursively
        elif prop_type == 'object' and 'properties' in prop_schema:
            print(f"\n  {label('Nested object:')} {colored(prop_name, Colors.BRIGHT_MAGENTA)}", file=sys.stderr)
            if description:
                print(f"  {label('Description:')} {description}", file=sys.stderr)
            nested_value = prompt_for_body_fields(prop_schema, full_schema, method, path)
            if nested_value:
                body[prop_name] = nested_value
            continue
        # Handle arrays
        elif prop_type == 'array':
            value = prompt_for_array_value(prop_name, is_required, prop_schema, full_schema, description)
        else:
            value = prompt_for_value(prop_name, is_required, prop_type, description, 'body')

        # Convert value to appropriate type
        if value:
            if prop_type == 'integer':
                try:
                    body[prop_name] = int(value)
                except ValueError:
                    print(f"  {error('Invalid integer, using as string')}", file=sys.stderr)
                    body[prop_name] = value
            elif prop_type == 'number':
                try:
                    body[prop_name] = float(value)
                except ValueError:
                    print(f"  {error('Invalid number, using as string')}", file=sys.stderr)
                    body[prop_name] = value
            elif prop_type == 'boolean':
                body[prop_name] = value.lower() in ('true', '1', 'yes')
            elif prop_type == 'array':
                body[prop_name] = value  # Already processed as array
            else:
                body[prop_name] = value
        elif is_required:
            # Include required fields with null value even if empty
            print(f"  {info('Required field left empty, including as null')}", file=sys.stderr)
            body[prop_name] = None

    if body:
        print("", file=sys.stderr)
        print(success("✓ Body built successfully"), file=sys.stderr)
        return body
    else:
        print(info("Empty body, skipping"), file=sys.stderr)
        return None


def prompt_for_enum_value(name, required, param_type, description, enum_values):
    """Prompt user to select from enum values using fzf."""
    print("", file=sys.stderr)
    print(f"  {label('Body field:')} \"{colored(name, Colors.BRIGHT_MAGENTA)}\"", file=sys.stderr)

    meta = []
    if required:
        meta.append(colored("REQUIRED", Colors.BRIGHT_RED))
    else:
        meta.append(colored("optional", Colors.YELLOW))
    if param_type:
        meta.append(colored(param_type, Colors.CYAN))
    meta.append(colored("enum", Colors.GREEN))

    print(f"  {label('Type:')} {', '.join(meta)}", file=sys.stderr)

    if description:
        print(f"  {label('Description:')} {description}", file=sys.stderr)

    # Use fzf to select from enum values
    try:
        enum_text = "\n".join(str(v) for v in enum_values)
        result = subprocess.run(
            ['fzf', '--height=40%', '--reverse', '--border', f'--prompt=Select {name}: '],
            input=enum_text,
            text=True,
            capture_output=True
        )
        if result.returncode == 0:
            selected = result.stdout.strip()
            print(f"  {success('✓ Selected:')} {selected}", file=sys.stderr)
            return selected
        else:
            print(f"  {info('No selection made')}", file=sys.stderr)
            return None
    except FileNotFoundError:
        # Fallback to manual input if fzf not found
        print(f"  {label('Options:')} {', '.join(str(v) for v in enum_values)}", file=sys.stderr)
        print(f"  {label('Enter value:')} ", end='', file=sys.stderr, flush=True)
        return input()


def prompt_for_array_value(name, required, prop_schema, full_schema, description):
    """Prompt user for array values."""
    print("", file=sys.stderr)
    print(f"  {label('Body field:')} \"{colored(name, Colors.BRIGHT_MAGENTA)}\"", file=sys.stderr)

    meta = []
    if required:
        meta.append(colored("REQUIRED", Colors.BRIGHT_RED))
    else:
        meta.append(colored("optional", Colors.YELLOW))
    meta.append(colored("array", Colors.CYAN))

    print(f"  {label('Type:')} {', '.join(meta)}", file=sys.stderr)

    if description:
        print(f"  {label('Description:')} {description}", file=sys.stderr)

    items_schema = prop_schema.get('items', {})
    if '$ref' in items_schema and full_schema:
        ref_path = items_schema['$ref']
        resolved = resolve_ref(full_schema, ref_path)
        if resolved:
            items_schema = resolved

    items_type = items_schema.get('type', 'string')

    # For arrays of objects, prompt for each object
    if items_type == 'object' and 'properties' in items_schema:
        array_values = []
        while True:
            print(f"\n  {info(f'Add item to {name}? (y/n):')} ", end='', file=sys.stderr, flush=True)
            add_more = input().strip().lower()
            if add_more not in ('y', 'yes'):
                break
            item_value = prompt_for_body_fields(items_schema, full_schema)
            if item_value:
                array_values.append(item_value)
        return array_values if array_values else None

    # For simple arrays (strings, UUIDs, etc.), prompt for comma-separated or one-by-one
    print(f"  {label('Items type:')} {items_type}", file=sys.stderr)

    # Check if items are UUIDs
    items_description = items_schema.get('description', '')
    if 'uuid' in name.lower() or 'uuid' in items_description.lower():
        array_values = []
        while True:
            print(f"\n  {info(f'Add UUID to {name}? (y/n):')} ", end='', file=sys.stderr, flush=True)
            add_more = input().strip().lower()
            if add_more not in ('y', 'yes'):
                break
            # Use fc-uuid for UUID selection
            try:
                cmd = ['fc-uuid']
                if _current_client_uuid:
                    cmd.extend(['--client', _current_client_uuid])
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                uuid_value = result.stdout.strip()
                if uuid_value:
                    array_values.append(uuid_value)
                    print(f"  {success('✓ Added:')} {uuid_value}", file=sys.stderr)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  {label('Enter UUID:')} ", end='', file=sys.stderr, flush=True)
                value = input().strip()
                if value:
                    array_values.append(value)
        return array_values if array_values else None

    # For other simple arrays, accept comma-separated values
    print(f"  {label('Enter values (comma-separated):')} ", end='', file=sys.stderr, flush=True)
    values_input = input().strip()
    if values_input:
        values = [v.strip() for v in values_input.split(',') if v.strip()]
        # Convert to appropriate type
        if items_type == 'integer':
            try:
                values = [int(v) for v in values]
            except ValueError:
                pass
        elif items_type == 'number':
            try:
                values = [float(v) for v in values]
            except ValueError:
                pass
        return values if values else None
    return None


def run_api_explorer(config, refresh=False):
    """Main entry point for API explorer.

    Args:
        config: Dict with keys:
            - schemas: List of schema configs, each with:
                - cache_file: Path to schema cache
                - schema_url: URL to fetch schema from
                - path_prefix: Prefix to prepend to all paths (e.g., '/v2')
            - base_url: API base URL
            - curl_command: Command to use for API calls
            - environment: Environment name (optional, default: 'local')
        refresh: If True, refresh cached schema data
    """
    global _current_client_uuid

    # Load all schemas with their prefixes
    schema_entries = []
    for schema_config in config['schemas']:
        schema = load_schema(
            schema_config['cache_file'],
            schema_config['schema_url'],
            config['base_url']
        )
        schema_entries.append({
            'schema': schema,
            'path_prefix': schema_config.get('path_prefix', '')
        })

    # Merge all schemas into one
    schema = merge_schemas(schema_entries)

    endpoints_text = format_endpoints(schema)
    if not endpoints_text:
        print(error("Error: No endpoints found in schema"), file=sys.stderr)
        sys.exit(1)

    selected = select_endpoint_with_fzf(endpoints_text)

    parts = selected.split(' -- ')[0].split(' ', 1)
    method = parts[0]
    path = parts[1]

    current_path = path

    # Process required headers from config first (e.g., x-sirius-client-uuid for BE API)
    headers = {}
    required_headers = config.get('required_headers', [])
    if required_headers:
        print(header("Required Headers"), file=sys.stderr)
        print("", file=sys.stderr)
        for rh in required_headers:
            name = rh['name']
            description = rh.get('description', '')

            value = prompt_for_value(name, True, 'string', description, 'header')

            if value:
                headers[name] = value
                if name.lower() == 'x-sirius-client-uuid':
                    _current_client_uuid = value
                    print(f"  {info('(will be used for fc-uuid filtering)')}", file=sys.stderr)
        print("", file=sys.stderr)

    # Process schema-defined headers, skipping any already provided by required_headers
    required_header_names = {rh['name'].lower() for rh in required_headers}
    header_params = get_parameters(schema, path, method, 'header')
    header_params = [p for p in header_params if p['name'].lower() not in required_header_names]
    if header_params:
        print(header("Header Parameters"), file=sys.stderr)
        print("", file=sys.stderr)
        for param in header_params:
            name = param['name']
            required = param.get('required', False)
            param_type = param.get('schema', {}).get('type', 'string')
            description = param.get('description', '')

            value = prompt_for_value(name, required, param_type, description, 'header')

            if value:
                headers[name] = value
                if name.lower() == 'x-sirius-client-uuid':
                    _current_client_uuid = value
                    print(f"  {info('(will be used for fc-uuid filtering)')}", file=sys.stderr)
        print("", file=sys.stderr)

    path_params = get_parameters(schema, path, method, 'path')
    if path_params:
        print(header("Path Parameters"), file=sys.stderr)
        print(f"{label('Building:')} {colored(config['base_url'] + current_path, Colors.BRIGHT_BLUE)}", file=sys.stderr)
        print("", file=sys.stderr)
        for param in path_params:
            name = param['name']
            required = param.get('required', False)
            param_type = param.get('schema', {}).get('type', 'string')
            description = param.get('description', '')

            value = prompt_for_value(name, required, param_type, description, 'path')

            current_path = current_path.replace(f"{{{name}}}", value)
        print("", file=sys.stderr)

    query_params = get_parameters(schema, path, method, 'query')
    query_string = ""
    if query_params:
        print(header("Query Parameters"), file=sys.stderr)
        print(f"{label('Building:')} {colored(config['base_url'] + current_path + '?...', Colors.BRIGHT_BLUE)}", file=sys.stderr)
        print("", file=sys.stderr)
        query_parts = []
        for param in query_params:
            name = param['name']
            required = param.get('required', False)
            param_type = param.get('schema', {}).get('type', 'string')
            description = param.get('description', '')

            value = prompt_for_value(name, required, param_type, description, 'query')

            if value:
                query_parts.append(f"{name}={value}")

        if query_parts:
            query_string = "?" + "&".join(query_parts)
        print("", file=sys.stderr)
    else:
        print(header("Query Parameters"), file=sys.stderr)
        print(info("No query parameters defined in schema."), file=sys.stderr)
        print("", file=sys.stderr)

    url = f"{config['base_url']}{current_path}{query_string}"

    request_body = None
    if method.upper() in ('POST', 'PUT', 'PATCH', 'DELETE'):
        body_schema = get_request_body_schema(schema, path, method)
        if body_schema:
            request_body = prompt_for_body_fields(body_schema, schema, method, path)

    command = f"{config['curl_command']}"

    environment = config.get('environment', 'local')
    if environment != 'local':
        command += f" --env {environment}"

    command += f" '{url}' -X {method}"

    for header_name, header_value in headers.items():
        command += f" -H '{header_name}: {header_value}'"

    if request_body:
        body_json = json.dumps(request_body)
        command += f" -d '{body_json}'"

    print(command)
