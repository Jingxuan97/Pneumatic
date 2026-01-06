# AWS Elastic Beanstalk Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **EB CLI** installed: `pip install awsebcli`
4. **PostgreSQL Database** (RDS instance or external)

## Step 1: Install EB CLI

```bash
pip install awsebcli
```

## Step 2: Initialize Elastic Beanstalk

```bash
# In project root
eb init -p python-3.10 pneumatic-chat --region us-east-1
```

This will:
- Create `.elasticbeanstalk/` directory
- Configure your AWS region
- Set up application name

## Step 3: Create Environment

```bash
eb create pneumatic-chat-prod \
  --instance-type t3.small \
  --platform "Python 3.10" \
  --single
```

For production with load balancing:
```bash
eb create pneumatic-chat-prod \
  --instance-type t3.small \
  --platform "Python 3.10" \
  --elb-type application \
  --envvars SECRET_KEY="your-secret-key-here",DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
```

## Step 4: Set Environment Variables

### Required Variables

```bash
# Set secret key (generate a secure random string)
eb setenv SECRET_KEY="your-very-secure-secret-key-minimum-32-characters"

# Set database URL
eb setenv DATABASE_URL="postgresql+asyncpg://user:password@host:5432/dbname"

# Set allowed origins (comma-separated)
eb setenv ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Optional: Rate limiting
eb setenv RATE_LIMIT_PER_MINUTE=60
eb setenv RATE_LIMIT_PER_HOUR=1000
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 5: Deploy

```bash
eb deploy
```

## Step 6: Check Status

```bash
eb status
eb health
eb logs
```

## Step 7: Open Application

```bash
eb open
```

## Database Setup

### Option A: RDS PostgreSQL

1. Create RDS PostgreSQL instance in AWS Console
2. Note the endpoint, port, database name
3. Set `DATABASE_URL` environment variable:
   ```
   postgresql+asyncpg://username:password@endpoint:5432/dbname
   ```

### Option B: External PostgreSQL

Use any PostgreSQL database and set `DATABASE_URL` accordingly.

### Initialize Database

The application will automatically create tables on first startup via `init_db()`.

## Health Checks

Elastic Beanstalk is configured to use `/ready` endpoint for health checks.

## Monitoring

- View logs: `eb logs`
- View health: `eb health`
- View environment: AWS Console → Elastic Beanstalk

## Updating Application

```bash
# Make changes to code
git add .
git commit -m "Update application"

# Deploy
eb deploy
```

## Scaling

### Enable Load Balancing

```bash
eb scale 2  # Scale to 2 instances
```

### Auto Scaling

Configure in AWS Console:
- Min instances: 1
- Max instances: 4
- Scaling triggers: CPU, NetworkIn, etc.

## Custom Domain

1. Get your EB environment URL
2. Configure DNS (Route 53 or your DNS provider)
3. Point domain to EB environment
4. Request SSL certificate in ACM
5. Configure HTTPS in EB environment

## Troubleshooting

### Check Logs
```bash
eb logs --all
```

### SSH into Instance
```bash
eb ssh
```

### View Environment Variables
```bash
eb printenv
```

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` format
   - Verify RDS security group allows EB security group
   - Check database is accessible

2. **Health Check Failing**
   - Verify `/ready` endpoint works
   - Check database connectivity
   - Review application logs

3. **CORS Errors**
   - Set `ALLOWED_ORIGINS` environment variable
   - Include protocol (https://) in origins

4. **Static Files Not Loading**
   - Check `.ebextensions/01_python.config` static files mapping
   - Verify `static/` directory is included in deployment

## Production Checklist

- [ ] `SECRET_KEY` set to secure random value
- [ ] `DATABASE_URL` points to production database
- [ ] `ALLOWED_ORIGINS` set to your domain(s)
- [ ] Database backups enabled
- [ ] SSL/HTTPS configured
- [ ] Health checks passing
- [ ] Monitoring/alerts configured
- [ ] Logs being collected (CloudWatch)

## Cost Optimization

- Use `t3.micro` or `t3.small` for development
- Enable auto-scaling to scale down during low traffic
- Use RDS `db.t3.micro` for small deployments
- Consider Reserved Instances for predictable workloads

## Security Best Practices

1. **Never commit secrets** - Use environment variables only
2. **Use HTTPS** - Configure SSL certificate
3. **Restrict CORS** - Set specific origins, not `*`
4. **Database Security** - Use RDS security groups
5. **Rate Limiting** - Already configured, adjust as needed
6. **Regular Updates** - Keep dependencies updated

## Next Steps

1. Set up RDS PostgreSQL database
2. Configure custom domain and SSL
3. Set up CloudWatch alarms
4. Configure auto-scaling
5. Set up CI/CD pipeline (optional)
