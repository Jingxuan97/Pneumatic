#!/bin/bash
# Script to fix AWS credentials for EB CLI

echo "=== AWS Credentials Fix Script ==="
echo ""

# Backup existing files
echo "1. Backing up existing credentials..."
cp ~/.aws/credentials ~/.aws/credentials.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp ~/.aws/config ~/.aws/config.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "   ✓ Backups created"
echo ""

# Check if credentials file exists and has valid format
echo "2. Checking credentials file..."
if [ -f ~/.aws/credentials ]; then
    # Check if default section exists and has valid keys
    if grep -q "\[default\]" ~/.aws/credentials; then
        if grep -q "aws_access_key_id" ~/.aws/credentials && grep -q "aws_secret_access_key" ~/.aws/credentials; then
            echo "   ✓ Default credentials section found"
        else
            echo "   ✗ Default section missing required keys"
        fi
    else
        echo "   ✗ No [default] section found"
    fi
else
    echo "   ✗ Credentials file not found"
fi
echo ""

# Fix config file - remove malformed eb-cli profile
echo "3. Fixing config file..."
if [ -f ~/.aws/config ]; then
    # Remove the malformed eb-cli profile section
    sed -i.bak '/^\[profile eb-cli\]/,/^\[/ { /^\[profile eb-cli\]/d; /^\[/!d; }' ~/.aws/config 2>/dev/null || \
    python3 -c "
import re
with open('$HOME/.aws/config', 'r') as f:
    content = f.read()
# Remove [profile eb-cli] section
content = re.sub(r'\[profile eb-cli\].*?(?=\[|$)', '', content, flags=re.DOTALL)
with open('$HOME/.aws/config', 'w') as f:
    f.write(content)
"
    echo "   ✓ Removed malformed eb-cli profile"
else
    echo "   ℹ Config file not found (will be created by aws configure)"
fi
echo ""

echo "4. Next steps:"
echo "   Run: aws configure"
echo "   Enter your valid AWS credentials"
echo "   Then test with: aws sts get-caller-identity"
echo "   Finally run: eb init"
echo ""
