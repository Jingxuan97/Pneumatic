# Elastic Beanstalk Deployment Guide

Clean, step-by-step guide to deploy Pneumatic Chat to AWS Elastic Beanstalk.

## Prerequisites

- AWS Account
- AWS CLI installed and configured (`aws configure`)
- EB CLI installed (`pip install awsebcli`)
- IAM permissions: `AWSElasticBeanstalkFullAccess`, `AmazonRDSFullAccess`, `AmazonEC2FullAccess`, `AmazonS3FullAccess`
- PostgreSQL RDS database created (see [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md) Part 2)

## Step 1: Prepare Environment Variables

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - this is your `SECRET_KEY`.

### Get Database URL

Format: `postgresql+asyncpg://username:password@host:port/database`

**From RDS Console:**
- Endpoint: `your-db.xxxxx.region.rds.amazonaws.com`
- Port: `5432` (default)
- Username: Your master username
- Password: Your master password
- Database: Your database name

**Example:**
```
postgresql+asyncpg://pneumatic_admin:MyPass123!@pneumatic-chat-db.abc123.eu-north-1.rds.amazonaws.com:5432/pneumatic_chat
```

**Important:** If password has special characters, URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`
- `+` → `%2B`
- `=` → `%3D`
- `?` → `%3F`

## Step 2: Initialize Elastic Beanstalk

```bash
# In project root
eb init
```

**Follow prompts:**
1. **Region**: Choose your region (e.g., `18` for eu-north-1)
   - **Important:** Must match your RDS region!
2. **Application name**: `pneumatic-chat` (or your choice)
3. **Platform**: Python
4. **Platform version**: Python 3.9, 3.11, or 3.12 (recommended)
5. **CodeCommit**: Answer **"n" (No)** - not needed
6. **SSH**: Yes (recommended for troubleshooting)
7. **Keypair**: Create new or select existing

## Step 3: Create Environment

```bash
eb create pneumatic-chat-prod \
  --instance-type t3.small \
  --platform "Python 3.9" \
  --elb-type application \
  --envvars SECRET_KEY="your-secret-key-here",DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname",ALLOWED_ORIGINS="*"
```

**Replace:**
- `your-secret-key-here` with your generated SECRET_KEY
- `user:pass@host:5432/dbname` with your actual DATABASE_URL values

**This takes 5-10 minutes** to create the environment.

## Step 4: Configure RDS Security Group

After environment is created:

### Get EB Security Group ID

**Method 1: AWS Console**
1. Go to EC2 → Instances
2. Find your EB instance (search for "pneumatic" or "elasticbeanstalk")
3. Click instance → Security tab → Click security group name

**Method 2: AWS CLI**
```bash
aws ec2 describe-instances \
  --region eu-north-1 \
  --filters "Name=tag:elasticbeanstalk:environment-name,Values=pneumatic-chat-prod" \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text
```

### Update RDS Security Group

1. Go to **RDS** → Your database → **Connectivity & security**
2. Click on the **security group** (under "VPC security groups")
3. Click **"Inbound rules"** tab
4. Click **"Edit inbound rules"**
5. Click **"Add rule"**:
   - **Type**: PostgreSQL
   - **Source**: Custom → Paste your EB security group ID
   - **Description**: Allow EB
6. Click **"Save rules"**

**Wait 1-2 minutes** for changes to propagate.

## Step 5: Verify Deployment

### Check Status

```bash
eb status
eb health --refresh
```

### Test Endpoints

```bash
# Get your URL from eb status
curl http://your-env-url.elasticbeanstalk.com/health
curl http://your-env-url.elasticbeanstalk.com/ready
```

**Expected:**
- `/health` → `{"status":"healthy"}`
- `/ready` → `{"status":"ready"}`

### Open Application

```bash
eb open
```

Or visit the CNAME URL from `eb status`.

## Step 6: Update Environment Variables (If Needed)

If you need to change environment variables:

```bash
eb setenv SECRET_KEY="new-key" \
         DATABASE_URL="new-url" \
         ALLOWED_ORIGINS="https://yourdomain.com"
```

Wait 2-3 minutes for update.

## Step 7: Deploy Updates

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Your changes"

# Deploy
eb deploy
```

Takes 3-5 minutes.

## Common Issues

### 502 Bad Gateway

**Most common cause:** Missing environment variables

**Fix:**
```bash
eb printenv  # Check what's set
eb setenv SECRET_KEY="..." DATABASE_URL="..."  # Set missing ones
```

### Health Status: Red

**Check logs:**
```bash
eb logs | tail -100
```

**Common fixes:**
- Set missing SECRET_KEY or DATABASE_URL
- Update RDS security group
- Restart environment: `eb restart`

### Database Connection Failed

**Check:**
1. DATABASE_URL is correct
2. RDS security group allows EB security group
3. Both are in same region
4. RDS is publicly accessible

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## Useful Commands

```bash
# Status and health
eb status
eb health

# Logs
eb logs
eb logs | tail -100
eb logs | grep -i error

# Environment variables
eb printenv
eb setenv KEY=value

# Deploy and restart
eb deploy
eb restart

# Open application
eb open

# SSH into instance
eb ssh

# List environments
eb list

# Terminate environment
eb terminate pneumatic-chat-prod
```

## Deployment Checklist

Before deploying, ensure:

- [ ] SECRET_KEY generated (32+ characters)
- [ ] DATABASE_URL ready (PostgreSQL connection string)
- [ ] RDS database created in same region as EB
- [ ] RDS security group allows EB security group
- [ ] IAM permissions configured
- [ ] AWS CLI and EB CLI installed
- [ ] Tests pass locally: `pytest`

After deployment:

- [ ] Environment status: Ready
- [ ] Health status: Green/Yellow
- [ ] `/health` endpoint returns 200
- [ ] `/ready` endpoint returns 200
- [ ] Application loads in browser
- [ ] Can sign up and login
- [ ] Can create conversations
- [ ] Messages work via WebSocket

## Next Steps

- [Complete AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md) - Full guide with RDS setup and domain configuration
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Architecture](ARCHITECTURE.md) - Technical details

## Quick Reference

**Required Environment Variables:**
- `SECRET_KEY` - 32+ character secret key
- `DATABASE_URL` - PostgreSQL connection string

**Optional:**
- `ALLOWED_ORIGINS` - CORS origins (default: "*")
- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 60)
- `RATE_LIMIT_PER_HOUR` - Rate limit (default: 1000)

**Important Notes:**
- EB and RDS must be in the **same region**
- RDS security group must allow EB security group
- SECRET_KEY must be 32+ characters
- DATABASE_URL must use `postgresql+asyncpg://` format
