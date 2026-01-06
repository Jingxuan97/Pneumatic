# Complete AWS Deployment Guide - Step by Step

This guide walks you through deploying Pneumatic Chat to AWS Elastic Beanstalk, including database setup and domain configuration.

## Prerequisites

- ✅ AWS Account (you have this)
- AWS CLI installed and configured
- EB CLI installed
- Your application code ready

---

## Part 1: Install Required Tools

### Step 1.1: Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download from: https://aws.amazon.com/cli/

### Step 1.2: Configure AWS CLI

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Get from AWS Console → IAM → Users → Your User → Security Credentials → Create Access Key
- **AWS Secret Access Key**: Shown when creating the access key (must be complete, ~40 characters)
- **Default region**: e.g., `us-east-1` or `us-west-2`
- **Default output format**: `json`

**Important:** Make sure your credentials file (`~/.aws/credentials`) has valid, complete entries. Do NOT use Python commands or placeholders in the credentials file.

**Verify configuration:**
```bash
aws sts get-caller-identity
```

This should return your AWS account information. If you get an error, see `FIX_AWS_CREDENTIALS.md` for troubleshooting.

### Step 1.2.1: Set Up IAM Permissions

**⚠️ Important:** Your IAM user needs permissions to use Elastic Beanstalk.

1. **Go to AWS Console** → IAM → Users → Your User (e.g., `cli-user`)

2. **Click "Add permissions"** → "Attach policies directly"

3. **Add these managed policies:**
   - `AWSElasticBeanstalkFullAccess` (required)
   - `AmazonRDSFullAccess` (for database setup)
   - `AmazonEC2FullAccess` (Elastic Beanstalk uses EC2)
   - `AmazonS3FullAccess` (Elastic Beanstalk uses S3)

4. **Click "Add permissions"**

5. **Wait 1-2 minutes** for permissions to propagate

6. **Verify permissions:**
   ```bash
   aws elasticbeanstalk describe-applications
   ```

   Should return successfully (may be empty list if no apps exist).

**If you get permission errors, see `FIX_IAM_PERMISSIONS.md` for detailed troubleshooting.**

### Step 1.3: Install EB CLI

```bash
pip install awsebcli
```

Verify installation:
```bash
eb --version
```

---

## Part 2: Set Up PostgreSQL Database (RDS)

### Step 2.1: Create RDS PostgreSQL Instance

1. **Go to AWS Console** → Search for "RDS" → Click "RDS"

2. **Click "Create database"**

3. **Choose configuration:**
   - **Database creation method**: Standard create
   - **Engine type**: PostgreSQL
   - **Version**: PostgreSQL 15.x or 16.x (latest stable)
   - **Template**: Free tier (for testing) or Production (for production)

4. **Settings:**
   - **DB instance identifier**: `pneumatic-chat-db`
   - **Master username**: `pneumatic_admin` (or your choice)
   - **Master password**: Create a strong password (save this!)
   - **Confirm password**: Re-enter password

5. **Instance configuration:**
   - **DB instance class**:
     - Free tier: `db.t3.micro` (for testing)
     - Production: `db.t3.small` or larger
   - **Storage**: 20 GB (minimum)

6. **Connectivity:**
   - **VPC**: Default VPC (or create new)
   - **Public access**: **Yes** (for Elastic Beanstalk access)
   - **VPC security group**: Create new
     - Name: `pneumatic-db-sg`
   - **Availability Zone**: No preference
   - **Database port**: `5432` (default PostgreSQL port)

7. **Database authentication**: Password authentication

8. **Additional configuration** (optional):
   - **Initial database name**: `pneumatic_chat`
   - **Backup retention**: 7 days (for production)

9. **Click "Create database"**

10. **Wait 5-10 minutes** for database to be created

### Step 2.2: Get Database Connection Details

1. **In RDS Console**, click on your database instance (`pneumatic-chat-db`)

2. **Note down:**
   - **Endpoint**: e.g., `pneumatic-chat-db.xxxxx.us-east-1.rds.amazonaws.com`
   - **Port**: `5432`
   - **Database name**: `pneumatic_chat` (or what you set)
   - **Username**: `pneumatic_admin` (or what you set)
   - **Password**: (the one you created)

3. **Your DATABASE_URL will be:**
   ```
   postgresql+asyncpg://pneumatic_admin:YOUR_PASSWORD@pneumatic-chat-db.xxxxx.us-east-1.rds.amazonaws.com:5432/pneumatic_chat
   ```

### Step 2.3: Configure Security Group

1. **In RDS Console**, click on your database → **Connectivity & security** tab

2. **Click on the VPC security group** (e.g., `pneumatic-db-sg`)

3. **In Security Group page:**
   - Click **Inbound rules** → **Edit inbound rules**
   - Click **Add rule**
   - **Type**: PostgreSQL
   - **Source**: Custom → Enter the security group ID of your Elastic Beanstalk environment
     - (We'll get this after creating EB environment, or use `0.0.0.0/0` temporarily for testing)
   - **Description**: Allow EB to connect
   - Click **Save rules**

**Note**: For production, restrict to only your EB security group. For testing, you can use `0.0.0.0/0` but change it later.

---

## Part 3: Set Up Domain Name (Optional but Recommended)

### Step 3.1: Register Domain (if you don't have one)

1. **Go to AWS Console** → Search for "Route 53" → Click "Route 53"

2. **Click "Registered domains"** → **Register domain**

3. **Search for your desired domain** (e.g., `mychatapp.com`)

4. **Add to cart** and complete purchase

5. **Wait 5-10 minutes** for domain registration

### Step 3.2: Use Existing Domain

If you already have a domain:
- You can transfer it to Route 53, or
- Use your existing DNS provider (GoDaddy, Namecheap, etc.)

---

## Part 4: Deploy to Elastic Beanstalk

### Step 4.1: Initialize Elastic Beanstalk

```bash
cd /Users/jingxuanyang/Projects/Pneumatic
eb init
```

**Follow the prompts:**
1. **Select a region**: Choose your region (e.g., `us-east-1`)
2. **Application name**: `pneumatic-chat` (or your choice)
3. **Platform**: Python
4. **Platform version**: Choose from available options:
   - **Python 3.11** or **3.12** (recommended - most stable and feature-complete)
   - **Python 3.9** (if you need older compatibility)
   - **Note**: Python 3.10 may not be available in all regions/platforms
5. **CodeCommit**: **Answer "n" (No)** - You don't need CodeCommit. Use local git and `eb deploy` instead.
6. **SSH**: Yes (recommended for troubleshooting)
7. **Keypair**: Create new or select existing

**Important:**
- When asked "Do you wish to continue with CodeCommit?", answer **"n" (No)**. CodeCommit is optional and requires additional IAM permissions. You can deploy using `eb deploy` without it.
- **Recommended**: Choose **Python 3.11** or **3.12** as they are well-supported and stable.

This creates `.elasticbeanstalk/` directory with configuration.

### Step 4.2: Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - this is your `SECRET_KEY`

### Step 4.3: Create Elastic Beanstalk Environment

```bash
eb create pneumatic-chat-prod \
  --instance-type t3.small \
  --platform "Python 3.11" \
  --elb-type application \
  --envvars SECRET_KEY="YOUR_SECRET_KEY_HERE",DATABASE_URL="postgresql+asyncpg://pneumatic_admin:YOUR_PASSWORD@pneumatic-chat-db.xxxxx.us-east-1.rds.amazonaws.com:5432/pneumatic_chat",ALLOWED_ORIGINS="https://yourdomain.com"
```

**Note:** Use `Python 3.11` or `Python 3.12` instead of `Python 3.10` as 3.10 may not be available in all regions.

**Replace:**
- `YOUR_SECRET_KEY_HERE` with the secret key from Step 4.2
- `YOUR_PASSWORD` with your RDS password
- `pneumatic-chat-db.xxxxx.us-east-1.rds.amazonaws.com` with your RDS endpoint
- `https://yourdomain.com` with your domain (or use `*` for testing)

**This will take 5-10 minutes** to create the environment.

### Step 4.4: Update Security Group (After EB Creation)

1. **Get EB Security Group:**
   ```bash
   eb status
   ```
   Note the "Security group" value

2. **Update RDS Security Group:**
   - Go to RDS → Your database → Security group
   - Edit inbound rules
   - Change source to the EB security group ID

### Step 4.5: Deploy Application

```bash
eb deploy
```

**This will:**
- Package your application
- Upload to S3
- Deploy to your EB environment
- Take 3-5 minutes

### Step 4.6: Check Deployment Status

```bash
eb status
eb health
```

### Step 4.7: View Application

```bash
eb open
```

This opens your application in the browser. You should see the login page!

---

## Part 5: Configure Custom Domain

### Step 5.1: Request SSL Certificate (ACM)

1. **Go to AWS Console** → Search for "Certificate Manager" → Click "ACM"

2. **Make sure you're in the same region as your EB environment** (top right)

3. **Click "Request certificate"**

4. **Choose:**
   - **Request a public certificate**
   - Click **Next**

5. **Domain names:**
   - **Fully qualified domain name**: `yourdomain.com`
   - **Add another name**: `www.yourdomain.com` (optional)
   - Click **Next**

6. **Validation:**
   - **DNS validation** (recommended)
   - Click **Next** → **Request**

7. **Validate certificate:**
   - Click on the certificate
   - Click **Create record in Route 53** (if using Route 53)
   - Or manually add CNAME records to your DNS provider
   - **Wait 5-10 minutes** for validation

### Step 5.2: Configure Domain in Route 53

1. **Go to Route 53** → **Hosted zones** → Click your domain

2. **Get EB Environment URL:**
   ```bash
   eb status
   ```
   Note the "CNAME" value (e.g., `pneumatic-chat-prod.eba-xxxxx.us-east-1.elasticbeanstalk.com`)

3. **Create A Record (Alias):**
   - Click **Create record**
   - **Record name**: Leave blank (for root domain) or `www` (for www subdomain)
   - **Record type**: A
   - **Alias**: Yes
   - **Route traffic to**: Alias to Application and Classic Load Balancer
   - **Region**: Your EB region
   - **Load balancer**: Select your EB load balancer
   - Click **Create records**

### Step 5.3: Configure HTTPS in Elastic Beanstalk

1. **Go to AWS Console** → **Elastic Beanstalk** → Your environment

2. **Configuration** → **Load balancer** → **Edit**

3. **Listeners:**
   - **Port 443** (HTTPS)
   - **Protocol**: HTTPS
   - **SSL certificate**: Select your ACM certificate
   - **Default process**: `default`
   - **Port**: `80`
   - **Protocol**: HTTP

4. **Click "Add listener"** for HTTP → HTTPS redirect:
   - **Port**: `80`
   - **Protocol**: HTTP
   - **Process**: `default`
   - **Action**: Redirect to HTTPS

5. **Click "Apply"** → Wait 2-3 minutes

### Step 5.4: Update Environment Variables

```bash
eb setenv ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

---

## Part 6: Initialize Database

### Step 6.1: Connect to Database and Create Tables

The application will automatically create tables on first startup, but you can verify:

1. **SSH into EB instance:**
   ```bash
   eb ssh
   ```

2. **Connect to database** (if you have psql installed):
   ```bash
   psql -h YOUR_RDS_ENDPOINT -U pneumatic_admin -d pneumatic_chat
   ```

3. **Or verify via application:**
   - Visit your application URL
   - Try to sign up
   - If it works, database is initialized!

---

## Part 7: Verify Deployment

### Step 7.1: Test Health Endpoints

```bash
# Health check
curl https://yourdomain.com/health

# Readiness check
curl https://yourdomain.com/ready

# Metrics
curl https://yourdomain.com/metrics
```

### Step 7.2: Test Application

1. **Visit**: `https://yourdomain.com`
2. **Sign up** for a new account
3. **Login** and test chat functionality

---

## Part 8: Post-Deployment Configuration

### Step 8.1: Set Up Auto Scaling

1. **EB Console** → Your environment → **Configuration** → **Capacity** → **Edit**

2. **Auto Scaling:**
   - **Min instances**: 1
   - **Max instances**: 4
   - **Scaling triggers**: CPU-based (e.g., scale up at 70% CPU)

3. **Click "Apply"**

### Step 8.2: Set Up CloudWatch Alarms

1. **Go to CloudWatch** → **Alarms** → **Create alarm**

2. **Metric**: Select your EB environment metrics
   - **Environment Health**: Red
   - **Application Requests 5xx**: > 0
   - **CPU Utilization**: > 80%

3. **Configure SNS notification** (optional)

### Step 8.3: Enable Database Backups

1. **RDS Console** → Your database → **Maintenance & backups**

2. **Automated backups**: Enabled
   - **Backup retention period**: 7 days (or your preference)

3. **Backup window**: Choose a low-traffic time

---

## Troubleshooting

### Issue: Can't connect to database

**Solution:**
1. Check RDS security group allows EB security group
2. Verify `DATABASE_URL` is correct
3. Check RDS is publicly accessible
4. Verify database is in "Available" state

### Issue: Health check failing

**Solution:**
```bash
eb logs
```
Check for errors in logs. Common issues:
- Database connection failed
- Missing environment variables
- Application errors

### Issue: Domain not resolving

**Solution:**
1. Verify DNS records in Route 53
2. Wait 5-10 minutes for DNS propagation
3. Check certificate is validated
4. Verify HTTPS listener is configured

### Issue: CORS errors

**Solution:**
```bash
eb setenv ALLOWED_ORIGINS="https://yourdomain.com"
eb deploy
```

### View Logs

```bash
# View recent logs
eb logs

# View specific log file
eb logs --all
```

### SSH into Instance

```bash
eb ssh
```

---

## Cost Estimation

### Free Tier (First 12 Months)
- **RDS**: `db.t3.micro` - Free (750 hours/month)
- **EC2**: `t3.micro` - Free (750 hours/month)
- **Elastic Beanstalk**: Free (just manages resources)
- **Route 53**: $0.50/month per hosted zone
- **Domain**: ~$12-15/year

**Total**: ~$1-2/month (mostly domain)

### Production (After Free Tier)
- **RDS**: `db.t3.small` - ~$15-20/month
- **EC2**: `t3.small` - ~$15/month
- **Data transfer**: ~$5-10/month
- **Route 53**: $0.50/month
- **Domain**: ~$12/year

**Total**: ~$35-50/month

---

## Quick Reference Commands

```bash
# Initialize EB
eb init

# Create environment
eb create pneumatic-chat-prod --envvars KEY=value

# Deploy
eb deploy

# View status
eb status
eb health

# View logs
eb logs

# SSH into instance
eb ssh

# Set environment variables
eb setenv KEY=value

# Open application
eb open

# Terminate environment (careful!)
eb terminate
```

---

## Next Steps

1. ✅ Set up monitoring and alerts
2. ✅ Configure automated backups
3. ✅ Set up CI/CD pipeline (optional)
4. ✅ Review security settings
5. ✅ Set up staging environment (optional)

---

## Support

- **AWS Documentation**: https://docs.aws.amazon.com/elasticbeanstalk/
- **EB CLI Docs**: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html
- **RDS Documentation**: https://docs.aws.amazon.com/rds/

Good luck with your deployment! 🚀
