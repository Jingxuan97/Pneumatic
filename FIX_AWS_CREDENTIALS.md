# Fix AWS Credentials Error

## Problem
The error `Invalid key=value pair (missing equal-sign) in Authorization header` indicates your AWS credentials are malformed.

**Your specific issue:** The `~/.aws/config` file has a malformed `[profile eb-cli]` section with a Python command instead of a real access key.

## Quick Fix (Automated)

Run this script to automatically fix the config file:

```bash
python3 fix_aws_config.py
```

This will:
1. Backup your current config
2. Remove the malformed `[profile eb-cli]` section
3. Show you the fixed config

Then test:
```bash
aws sts get-caller-identity
eb init
```

## Manual Solution

### Option 1: Reconfigure AWS CLI (Recommended)

1. **Back up your current credentials:**
   ```bash
   cp ~/.aws/credentials ~/.aws/credentials.backup
   cp ~/.aws/config ~/.aws/config.backup
   ```

2. **Reconfigure AWS CLI:**
   ```bash
   aws configure
   ```

   You'll need:
   - **AWS Access Key ID**: From AWS Console → IAM → Users → Your User → Security Credentials
   - **AWS Secret Access Key**: From the same location (create new if needed)
   - **Default region**: e.g., `us-west-2` or `us-east-1`
   - **Default output format**: `json`

3. **Verify the credentials file is correct:**
   ```bash
   cat ~/.aws/credentials
   ```

   Should look like:
   ```
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY_ID
   aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
   ```

4. **Test AWS CLI:**
   ```bash
   aws sts get-caller-identity
   ```

   Should return your AWS account info.

### Option 2: Fix the Config File Manually

1. **Edit the config file:**
   ```bash
   nano ~/.aws/config
   ```

2. **Remove or fix the `[profile eb-cli]` section** - it has malformed entries:
   ```
   [profile eb-cli]
   aws_access_key_id = python -c "import secrets; print(secrets.token_urlsafe(32))  # THIS IS WRONG
   aws_secret_access_key = ENTER_SECRET_HERE  # THIS IS WRONG
   ```

   Either delete this entire section, or fix it with real credentials:
   ```
   [profile eb-cli]
   aws_access_key_id = YOUR_REAL_ACCESS_KEY
   aws_secret_access_key = YOUR_REAL_SECRET_KEY
   region = us-west-2
   ```

3. **Check your credentials file:**
   ```bash
   cat ~/.aws/credentials
   ```

   Make sure the `[default]` section has complete, valid credentials.

### Option 3: Create New Access Keys

If your credentials are invalid or expired:

1. **Go to AWS Console** → IAM → Users → Your User
2. **Click "Security credentials" tab**
3. **Under "Access keys"**, click "Create access key"
4. **Choose "Command Line Interface (CLI)"**
5. **Download or copy the keys**
6. **Run `aws configure`** and enter the new keys

### Verify Fix

After fixing, test:
```bash
aws sts get-caller-identity
```

Then try `eb init` again.

## Common Issues

- **Incomplete secret key**: Secret keys should be ~40 characters long
- **Malformed config**: No Python commands or placeholders in credential files
- **Wrong region**: Make sure region matches where you want to deploy
- **Expired keys**: Create new access keys if old ones are expired
