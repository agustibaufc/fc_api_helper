#!/bin/bash
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

# Install package
pip install -e .

# Create zsh functions file
cat > ~/.zsh_functions << 'EOF'
# FC API Helper - Zsh wrappers (inject output into prompt)
be-api() {
    local out=$(command be-api "$@")
    [ $? -eq 0 ] && [ -n "$out" ] && print -z "$out"
}
dpl-api() {
    local out=$(command dpl-api "$@")
    [ $? -eq 0 ] && [ -n "$out" ] && print -z "$out"
}
fc-uuid() {
    local out=$(command fc-uuid "$@")
    [ $? -eq 0 ] && [ -n "$out" ] && print -z "$out"
}
EOF

# Source from .zshrc if not already
grep -q 'source ~/.zsh_functions' ~/.zshrc || echo 'source ~/.zsh_functions' >> ~/.zshrc

echo "Done! Run: source ~/.zshrc"
