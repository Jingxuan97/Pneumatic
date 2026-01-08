# Debugging Guide

Common issues and solutions for Pneumatic Chat.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Database Issues](#database-issues)
3. [Application Errors](#application-errors)
4. [Frontend Issues](#frontend-issues)
5. [WebSocket Issues](#websocket-issues)

---

## Deployment Issues

### 502 Bad Gateway

**Symptoms:**
- Application returns 502 Bad Gateway
- `/ready` endpoint returns 503
- Health status is Red

**Common Causes:**

#### 1. Missing Environment Variables

**Check:**
```bash
eb printenv
```

**Must have:**
- `SECRET_KEY` - 32+ characters
- `DATABASE_URL` - PostgreSQL connection string

**Fix:**
```bash
eb setenv SECRET_KEY="your-secret-key" \
         DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname" \
         ALLOWED_ORIGINS="*"
```

Wait 2-3 minutes, then test again.

#### 2. Security Group Not Configured

**Problem:** RDS security group doesn't allow EB security group

**Solution:**
1. Get EB security group: AWS Console → EC2 → Instances → Your instance → Security tab
2. Go to RDS → Your database → Connectivity & security
3. Click security group → Inbound rules → Edit
4. Add rule: Type=PostgreSQL, Source=EB security group ID
5. Save rules
6. Wait 1-2 minutes

#### 3. Wrong Region

**Problem:** EB and RDS in different regions

**Solution:**
- Ensure both are in the same region
- If different, move one to match the other

#### 4. DATABASE_URL Format Incorrect

**Check format:**
```
postgresql+asyncpg://username:password@host:port/database
```

**Common mistakes:**
- Missing `+asyncpg` driver
- Wrong port (should be 5432)
- Special characters in password not URL-encoded
- Wrong endpoint

**URL-encode special characters:**
- `@` → `%40`, `#` → `%23`, `$` → `%24`, `%` → `%25`, `&` → `%26`, `+` → `%2B`, `=` → `%3D`, `?` → `%3F`

### Environment Already Exists

**Error:** `Environment pneumatic-chat-prod already exists`

**Solutions:**

**Option 1: Use existing**
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

### Environment in Invalid State

**Error:** `Environment is in an invalid state for this operation. Must be Ready.`

**Solution:**
1. Wait 5-10 minutes for environment to finish updating
2. Check status: `eb status`
3. Once status is "Ready", retry your command

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

---

## Database Issues

### Database Connection Failed

**Symptoms:**
- `/ready` endpoint returns 503
- Application logs show connection errors

**Solutions:**

1. **Check DATABASE_URL format:**
   ```
   postgresql+asyncpg://username:password@host:port/database
   ```

2. **Verify RDS is publicly accessible:**
   - RDS → Your database → Connectivity & security
   - "Publicly accessible" should be "Yes"

3. **Check security group:**
   - RDS security group must allow EB security group
   - See "Security Group Not Configured" above

4. **Test connection locally:**
   ```python
   import asyncpg
   conn = await asyncpg.connect("postgresql://user:pass@host:5432/dbname")
   ```

### Timezone Mismatch Error

**Error:**
```
invalid input for query argument: datetime.datetime(...)
(can't subtract offset-naive and offset-aware datetimes)
```

**Cause:**
- Database column expects naive datetime (`timezone=False`)
- Code is using timezone-aware datetime

**Solution:**
- Already fixed in codebase
- If you see this, ensure you're using the latest version

---

## Application Errors

### Import Error: Request Not Defined

**Error:**
```
NameError: name 'Request' is not defined
```

**Solution:**
- Already fixed in `app/auth.py`
- Ensure `from fastapi import Request` is present

### AsyncIO Event Loop Error

**Error:**
```
RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Cause:**
- `asyncio.Lock()` created at import time (before event loop exists)

**Solution:**
- Already fixed with lazy initialization
- Locks are created when first needed (event loop exists)

### Application Crash on Startup

**Check logs:**
```bash
eb logs | tail -100
```

**Common causes:**
1. Missing environment variables
2. Database connection failure
3. Import errors
4. Syntax errors

**Fix based on logs:**
- If SECRET_KEY error: Set proper SECRET_KEY (32+ chars)
- If database error: Check DATABASE_URL and security groups
- If import error: Check requirements.txt

---

## Frontend Issues

### Send Button Not Working

**Symptoms:**
- Clicking send button does nothing
- Console shows errors

**Solutions:**

1. **Check for duplicate event listeners:**
   - Remove redundant `onclick` or event listeners
   - Use either `onclick` attribute OR `addEventListener`, not both

2. **Check WebSocket connection:**
   - Ensure WebSocket is connected (check connection status indicator)
   - Reconnect if needed

3. **Check console for errors:**
   - Open browser DevTools → Console
   - Look for JavaScript errors

### Messages Not Appearing in Real-Time

**Symptoms:**
- Messages sent but not received
- Need to refresh page to see messages

**Solutions:**

1. **Check WebSocket connection:**
   - Ensure WebSocket is connected
   - Check connection status indicator

2. **Check console logs:**
   - Look for WebSocket errors
   - Check if messages are being received

3. **Verify conversation is joined:**
   - Check console for "Joined conversation" message
   - Ensure `currentConversationId` matches received message's conversation_id

4. **Check for duplicate prevention:**
   - Messages with same `message_id` are skipped
   - Ensure each message has unique `message_id`

### crypto.randomUUID() Not Available

**Error:**
```
Uncaught TypeError: crypto.randomUUID is not a function
```

**Solution:**
- Already fixed with fallback implementation
- Uses `crypto.randomUUID()` if available, otherwise generates UUID manually

---

## WebSocket Issues

### WebSocket Connection Fails

**Symptoms:**
- WebSocket connection closes immediately
- 502 error on WebSocket endpoint

**Solutions:**

1. **Check authentication:**
   - Ensure token is valid
   - Token should be in query: `?token=YOUR_TOKEN`

2. **Check server logs:**
   ```bash
   eb logs | grep websocket
   ```

3. **Verify endpoint:**
   - Should be `wss://your-domain.com/ws?token=...` (production)
   - Or `ws://localhost:8000/ws?token=...` (local)

### Messages Not Broadcasting

**Symptoms:**
- Message sent successfully
- Other users don't receive it

**Solutions:**

1. **Check WebSocket connection:**
   - Ensure all users have active WebSocket connections
   - Check connection status indicator

2. **Verify conversation membership:**
   - Ensure users are members of the conversation
   - Check database for conversation members

3. **Check server logs:**
   - Look for broadcast errors
   - Check if messages are being saved

### WebSocket Closes After Message

**Symptoms:**
- WebSocket closes immediately after sending message
- Connection reconnects but messages lost

**Solution:**
- Already fixed with improved error handling
- Exceptions no longer close the connection
- Errors are sent to client instead

---

## Health Check Issues

### Health Check Failing

**Test endpoints:**
```bash
curl http://your-env-url.elasticbeanstalk.com/health
curl http://your-env-url.elasticbeanstalk.com/ready
```

**Expected:**
- `/health` → `{"status":"healthy"}`
- `/ready` → `{"status":"ready"}` or 503 if database unavailable

**If failing:**
1. Check application logs: `eb logs`
2. Verify environment variables: `eb printenv`
3. Check database connection
4. Verify application is running: `eb status`

---

## Getting Help

### View Logs

```bash
# Elastic Beanstalk logs
eb logs

# Specific log files
eb logs | grep -A 20 "ERROR"

# Real-time logs
eb logs --stream
```

### Check Status

```bash
# Environment status
eb status

# Health status
eb health --refresh

# Environment variables
eb printenv
```

### Test Locally

Before deploying, test locally:
```bash
# Set environment variables
export SECRET_KEY="test-key-32-characters-minimum"
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"

# Run server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `502 Bad Gateway` | App not starting | Check logs, verify env vars |
| `503 Service Unavailable` | Database unavailable | Check DATABASE_URL, security groups |
| `429 Too Many Requests` | Rate limit exceeded | Wait, or increase limits |
| `401 Unauthorized` | Invalid token | Re-login, check token expiration |
| `403 Forbidden` | Not a member | Verify conversation membership |
| `404 Not Found` | Resource missing | Check IDs, verify existence |

---

## Prevention Tips

1. **Always test locally first** before deploying
2. **Check environment variables** before deployment
3. **Verify security groups** are configured correctly
4. **Monitor logs** after deployment
5. **Test health endpoints** after deployment
6. **Use strong passwords** for RDS
7. **Keep dependencies updated**
8. **Review error messages** carefully

---

## Next Steps

- **Deployment**: See `DEPLOYMENT.md` for deployment guide
- **Tutorial**: See `TUTORIAL.md` for feature guide
- **Quick Start**: See `QUICK_START.md` for local development
