# Deployment Guide

Complete guide to deploying Pneumatic Chat to AWS Elastic Beanstalk.

## Prerequisites

- AWS Account
- AWS CLI installed and configured (`aws configure`)
- EB CLI installed (`pip install awsebcli`)
- IAM permissions: `AWSElasticBeanstalkFullAccess`, `AmazonRDSFullAccess`, `AmazonEC2FullAccess`, `AmazonS3FullAccess`

---

## Quick Deployment

### Step 1: Prepare Environment Variables

**Generate Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Get Database URL:**
Format: `postgresql+asyncpg://username:password@host:port/database`

From RDS Console:
- Endpoint: `your-db.xxxxx.region.rds.amazonaws.com`
- Port: `5432`
- Username: Your master username
- Password: Your master password
- Database: Your database name (often `postgres`)

**Example:**
```
postgresql+asyncpg://pneumatic_admin:MyPass123!@pneumatic-chat-db.abc123.eu-north-1.rds.amazonaws.com:5432/postgres
```

**Important:** URL-encode special characters in password:
- `@` → `%40`, `#` → `%23`, `$` → `%24`, `%` → `%25`, `&` → `%26`, `+` → `%2B`, `=` → `%3D`, `?` → `%3F`

### Step 2: Initialize Elastic Beanstalk

```bash
eb init
```

**Follow prompts:**
1. **Region**: Choose your region (must match RDS region!)
2. **Application name**: `pneumatic-chat`
3. **Platform**: Python
4. **Platform version**: Python 3.9, 3.11, or 3.12
5. **CodeCommit**: Answer **"n" (No)**
6. **SSH**: Yes (recommended)
7. **Keypair**: Create new or select existing

### Step 3: Create Environment

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

### Step 4: Configure RDS Security Group

**Get EB Security Group ID:**

**Method 1: AWS Console**
1. Go to EC2 → Instances
2. Find your EB instance
3. Click instance → Security tab → Click security group name

**Method 2: AWS CLI**
```bash
aws ec2 describe-instances \
  --region eu-north-1 \
  --filters "Name=tag:elasticbeanstalk:environment-name,Values=pneumatic-chat-prod" \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text
```

**Update RDS Security Group:**
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

### Step 5: Verify Deployment

**Check Status:**
```bash
eb status
eb health --refresh
```

**Test Endpoints:**
```bash
# Get your URL from eb status
curl http://your-env-url.elasticbeanstalk.com/health
curl http://your-env-url.elasticbeanstalk.com/ready
```

**Expected:**
- `/health` → `{"status":"healthy"}`
- `/ready` → `{"status":"ready"}`

**Open Application:**
```bash
eb open
```

---

## Setting Up PostgreSQL Database (RDS)

### Create RDS Instance

1. **Go to AWS Console** → RDS → Create database

2. **Configuration:**
   - **Engine**: PostgreSQL
   - **Version**: 15.x or 16.x
   - **Template**: Free tier (testing) or Production
   - **DB instance identifier**: `pneumatic-chat-db`
   - **Master username**: `pneumatic_admin`
   - **Master password**: Create strong password (save it!)
   - **DB instance class**: `db.t3.micro` (free tier) or `db.t3.small` (production)
   - **Storage**: 20 GB minimum
   - **Public access**: **Yes**
   - **VPC security group**: Create new (`pneumatic-db-sg`)
   - **Database port**: `5432`
   - **Initial database name**: `postgres` (or your choice)

3. **Click "Create database"**

4. **Wait 5-10 minutes** for creation

### Get Connection Details

From RDS Console → Your database:
- **Endpoint**: `pneumatic-chat-db.xxxxx.region.rds.amazonaws.com`
- **Port**: `5432`
- **Database name**: `postgres` (or what you set)
- **Username**: `pneumatic_admin`
- **Password**: (the one you created)

**DATABASE_URL format:**
```
postgresql+asyncpg://pneumatic_admin:YOUR_PASSWORD@pneumatic-chat-db.xxxxx.region.rds.amazonaws.com:5432/postgres
```

---

## Updating Environment Variables

```bash
eb setenv SECRET_KEY="new-key" \
         DATABASE_URL="new-url" \
         ALLOWED_ORIGINS="*"
```

Wait 2-3 minutes for changes to apply.

---

## Deploying Code Updates

```bash
# Make your code changes
# Then deploy:
eb deploy

# Check status:
eb status
eb health --refresh
```

---

## Domain Name Setup (Optional)

### Using Route 53

1. **Register domain** in Route 53 (or use existing)

2. **Create hosted zone** for your domain

3. **Create record set:**
   - **Type**: CNAME
   - **Name**: `chat` (or `www`, or leave blank for root)
   - **Value**: Your EB environment CNAME (from `eb status`)

4. **Update nameservers** at your domain registrar

5. **Wait 5-10 minutes** for DNS propagation

### SSL Certificate

1. **Request certificate** in AWS Certificate Manager (ACM)
2. **Validate** via DNS or email
3. **Configure** in Elastic Beanstalk → Configuration → Load balancer → Add listener
   - **Protocol**: HTTPS
   - **Port**: 443
   - **SSL certificate**: Select your certificate

---

## Production Checklist

- [ ] PostgreSQL RDS instance created
- [ ] RDS security group allows EB security group
- [ ] `SECRET_KEY` set (32+ characters)
- [ ] `DATABASE_URL` correctly formatted
- [ ] `ALLOWED_ORIGINS` set to your domain
- [ ] Health checks passing (`/health`, `/ready`)
- [ ] Domain name configured (optional)
- [ ] SSL certificate configured (optional)
- [ ] Environment variables verified (`eb printenv`)

---

## Common Issues

See `DEBUG.md` for detailed troubleshooting of:
- 502 Bad Gateway errors
- Database connection failures
- Environment variable issues
- Security group configuration
- Health check failures

---

## Monitoring

**View Logs:**
```bash
eb logs
```

**Check Metrics:**
```bash
curl http://your-env-url.elasticbeanstalk.com/metrics
```

**Health Status:**
```bash
eb health --refresh
```

---

## Scaling

**Auto Scaling:**
- Configure in EB Console → Configuration → Capacity
- Set min/max instances
- Configure triggers based on CPU, network, etc.

**Manual Scaling:**
```bash
eb scale 2  # Scale to 2 instances
```

---

## Backup & Recovery

**Database Backups:**
- RDS automatically creates daily backups
- Retention period: 7 days (configurable)
- Manual snapshots can be created in RDS Console

**Application Version:**
- EB keeps previous versions
- Rollback: `eb deploy --version-label <version>`

---

## Cost Optimization

- Use `t3.micro` instances for development
- Use RDS free tier for testing
- Enable auto-scaling to scale down during low traffic
- Use reserved instances for production (if committed)

---

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use strong passwords** - For RDS and SECRET_KEY
3. **Restrict security groups** - Only allow necessary traffic
4. **Enable HTTPS** - Use SSL certificates
5. **Regular updates** - Keep dependencies updated
6. **Monitor logs** - Check for suspicious activity

---

## Next Steps

- **Tutorial**: See `TUTORIAL.md` for feature guide
- **Debugging**: See `DEBUG.md` for troubleshooting
- **Quick Start**: See `QUICK_START.md` for local development
