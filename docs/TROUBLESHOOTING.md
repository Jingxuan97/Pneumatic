# Troubleshooting Guide

Common issues and solutions for deploying Pneumatic Chat to AWS Elastic Beanstalk.

## Table of Contents

1. [Environment Setup Issues](#environment-setup-issues)
2. [Deployment Issues](#deployment-issues)
3. [Database Connection Issues](#database-connection-issues)
4. [Application Health Issues](#application-health-issues)
5. [Common Error Messages](#common-error-messages)

---

## Environment Setup Issues

### AWS Credentials Error

**Error:** `Invalid key=value pair (missing equal-sign) in Authorization header`

**Solution:**
1. Check `~/.aws/config` for malformed entries
2. Remove any `[profile eb-cli]` sections with invalid values
3. Run `aws configure` to reconfigure credentials
4. Verify: `aws sts get-caller-identity`

### IAM Permissions Error

**Error:** `User is not authorized to perform: elasticbeanstalk:CreateApplication`

**Solution:**
1. Go to AWS Console → IAM → Users → Your User
2. Add permissions → Attach policies directly
3. Add: `AWSElasticBeanstalkFullAccess`, `AmazonRDSFullAccess`, `AmazonEC2FullAccess`, `AmazonS3FullAccess`
4. Wait 1-2 minutes, then retry

### CodeCommit Error During `eb init`

**Error:** `User is not authorized to perform: codecommit:ListRepositories`

**Solution:**
- Answer **"n" (No)** when asked about CodeCommit
- CodeCommit is optional - you can use `eb deploy` without it

---

## Deployment Issues

### Environment Already Exists

**Error:** `Environment pneumatic-chat-prod already exists`

**Solutions:**

**Option 1: Use existing environment**
```bash
eb use pneumatic-chat-prod
eb deploy
```

**Option 2: Terminate and recreate**
```bash
eb terminate pneumatic-chat-prod
# Wait 5-10 minutes
eb create pneumatic-chat-prod --envvars ...
```

**Option 3: Use different name**
```bash
eb create pneumatic-chat-prod-v2 --envvars ...
```

### Invalid Health Check Configuration

**Error:** `Invalid option specification: HealthCheckURL`

**Solution:**
- The `.ebextensions/02_healthcheck.config` has been fixed
- If you see this error, ensure you have the latest version
- The invalid `HealthCheckURL` option has been removed

### Environment in Invalid State

**Error:** `Environment is in an invalid state for this operation. Must be Ready.`

**Solution:**
1. Wait 5-10 minutes for environment to finish updating/launching
2. Check status: `eb status` or AWS Console
3. Once status is "Ready", retry your command

---

## Database Connection Issues

### 502 Bad Gateway / Database Connection Failed

**Symptoms:**
- Application returns 502 Bad Gateway
- `/ready` endpoint returns 503
- Health status is Red

**Common Causes & Solutions:**

#### 1. Missing Environment Variables (Most Common)

**Check:**
```bash
eb printenv
```

**Must have:**
- `SECRET_KEY` - 32+ characters
- `DATABASE_URL` - PostgreSQL connection string

**Fix:**
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set environment variables
eb setenv SECRET_KEY="your-secret-key" \
         DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname" \
         ALLOWED_ORIGINS="*"
```

Wait 2-3 minutes, then test again.

#### 2. Security Group Not Configured

**Problem:** RDS security group doesn't allow EB security group

**Solution:**
1. Get EB security group: `eb status` (or AWS Console → EC2 → Instances → Your instance → Security tab)
2. Go to RDS → Your database → Connectivity & security
3. Click on security group → Inbound rules → Edit
4. Add rule: Type=PostgreSQL, Source=EB security group ID
5. Save rules
6. Wait 1-2 minutes

#### 3. Wrong Region

**Problem:** EB and RDS in different regions

**Solution:**
- Ensure both are in the same region (e.g., both in `eu-north-1`)
- If different, either:
  - Move EB to RDS region, or
  - Move RDS to EB region

#### 4. DATABASE_URL Format Incorrect

**Check format:**
```
postgresql+asyncpg://username:password@host:port/database
```

**Common mistakes:**
- Missing `+asyncpg` driver
- Wrong port (should be 5432)
- Special characters in password not URL-encoded
- Wrong endpoint (should match RDS endpoint exactly)

#### 5. RDS Not Publicly Accessible

**Check:**
- RDS → Your database → Connectivity & security
- "Publicly accessible" should be "Yes"

**If "No":**
- Modify database → Publicly accessible → Yes
- Apply changes (requires restart, 5-10 minutes)

---

## Application Health Issues

### Health Status: Red

**Check logs:**
```bash
eb logs | tail -100
```

**Common issues:**
1. Application crash on startup
2. Missing environment variables
3. Database connection failure
4. Import errors

**Fix based on logs:**
- If SECRET_KEY error: Set proper SECRET_KEY (32+ chars)
- If database error: Check DATABASE_URL and security groups
- If import error: Check requirements.txt has all dependencies

### Health Check Endpoint Failing

**Test endpoints:**
```bash
curl http://your-env-url.elasticbeanstalk.com/health
curl http://your-env-url.elasticbeanstalk.com/ready
```

**Expected:**
- `/health` should return: `{"status":"healthy"}`
- `/ready` should return: `{"status":"ready"}` (tests database)

**If `/ready` returns 503:**
- Database connection is failing
- Check DATABASE_URL and security groups

---

## Common Error Messages

### `ValueError: SECRET_KEY must be at least 32 characters long`

**Fix:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
eb setenv SECRET_KEY="generated-key-here"
```

### `ModuleNotFoundError: No module named 'X'`

**Fix:**
1. Check `requirements.txt` has the module
2. Redeploy: `eb deploy`

### `Connection refused` or `could not connect to server`

**Fix:**
1. Verify DATABASE_URL is correct
2. Check RDS security group allows EB security group
3. Verify RDS is publicly accessible
4. Check both are in same region

### `502 Bad Gateway`

**Causes:**
- Application not starting
- Application crashing
- Missing environment variables

**Fix:**
1. Check logs: `eb logs | tail -100`
2. Check environment variables: `eb printenv`
3. Set missing variables: `eb setenv KEY=value`
4. Restart: `eb restart`

### `RuntimeError: There is no current event loop in thread 'MainThread'`

**⚠️ CRITICAL BUG: AsyncIO Lock Initialization at Import Time**

This is a **nasty production bug** that causes the application to fail silently on startup when using Gunicorn/Uvicorn workers.

**Error Message:**
```
RuntimeError: There is no current event loop in thread 'MainThread'.
File ".../app/websockets.py", line 13, in __init__
    self.lock = asyncio.Lock()
```

**Root Cause:**
- `asyncio.Lock()` requires an active event loop to be created
- When Python imports modules (at startup), there is **no event loop running yet**
- Gunicorn workers import your application module **before** starting the async event loop
- Creating `asyncio.Lock()` in `__init__` methods or at module level fails because no event loop exists

**Why It's Nasty:**
1. **Silent failure**: Application appears to deploy successfully but crashes immediately
2. **Hard to debug**: Error only appears in production logs, not during local development (where event loop may already exist)
3. **Affects all workers**: All Gunicorn workers fail to boot, causing 502 errors
4. **Easy to miss**: Code works fine in development but fails in production

**Affected Code Patterns:**
```python
# ❌ BAD - Creates lock at import time
class ConnectionManager:
    def __init__(self):
        self.lock = asyncio.Lock()  # FAILS - no event loop yet!

# ❌ BAD - Creates lock at module level
lock = asyncio.Lock()  # FAILS - no event loop yet!
```

**Solution: Lazy Initialization**

Create the lock only when it's first needed (inside an async method where event loop exists):

```python
# ✅ GOOD - Lazy initialization
class ConnectionManager:
    def __init__(self):
        self._lock = None  # No lock created yet

    def _get_lock(self):
        """Create lock lazily when first needed (in async context)."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def connect(self, user_id: str, websocket: WebSocket):
        async with self._get_lock():  # Lock created here (event loop exists)
            # ... your code
```

**Files That Had This Bug:**
- `app/websockets.py` - `ConnectionManager.__init__()` created lock at import time
- `app/rate_limit.py` - `RateLimiter.__init__()` created lock at import time

**How to Prevent:**
1. **Never create `asyncio.Lock()` in `__init__` methods** that are called at import time
2. **Never create `asyncio.Lock()` at module level**
3. **Always use lazy initialization** - create the lock inside async methods when first needed
4. **Test with Gunicorn locally** before deploying:
   ```bash
   gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker
   ```

**How to Identify:**
1. Check logs: `eb logs | grep -i "event loop"`
2. Look for: `RuntimeError: There is no current event loop`
3. Check stack trace - it will point to `asyncio.Lock()` creation
4. Application fails to start - all workers crash immediately

**Additional Notes:**
- This bug is **Python 3.9+ specific** when using `uvloop` (which Gunicorn uses)
- In Python 3.7/3.8, `asyncio.Lock()` might work differently, but still avoid it
- The same issue applies to other asyncio primitives: `asyncio.Event()`, `asyncio.Condition()`, etc.
- Always test your production deployment setup locally before deploying

---

## Quick Diagnostic Commands

```bash
# Check environment status
eb status

# Check health
eb health --refresh

# Check environment variables
eb printenv

# Get recent errors
eb logs | grep -i error | tail -20

# Get last 50 lines of logs
eb logs | tail -50

# Test endpoints
curl http://your-env-url.elasticbeanstalk.com/health
curl http://your-env-url.elasticbeanstalk.com/ready

# Restart environment
eb restart
```

---

## Getting Help

1. **Check logs first:** `eb logs | tail -100`
2. **Check environment variables:** `eb printenv`
3. **Check AWS Console:** Elastic Beanstalk → Your environment → Events/Logs
4. **Review this guide** for your specific error
5. **Check AWS documentation:** https://docs.aws.amazon.com/elasticbeanstalk/

---

## Prevention Checklist

Before deploying, ensure:

- [ ] SECRET_KEY is generated (32+ characters)
- [ ] DATABASE_URL is correct and points to same region as EB
- [ ] RDS security group allows EB security group
- [ ] RDS is publicly accessible (or VPC configured properly)
- [ ] Both EB and RDS are in the same region
- [ ] All dependencies in requirements.txt
- [ ] Tests pass locally: `pytest`
- [ ] Application runs locally with production DATABASE_URL
