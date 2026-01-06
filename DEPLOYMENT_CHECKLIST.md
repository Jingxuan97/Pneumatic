# Deployment Checklist

Use this checklist before deploying to ensure everything is ready.

## Pre-Deployment

- [ ] All tests pass: `pytest`
- [ ] No local database files (`dev.db`) in repository
- [ ] `.gitignore` is properly configured
- [ ] All environment variables documented
- [ ] Code is committed to git

## Environment Variables Required

Before deploying, ensure you have:

- [ ] `SECRET_KEY` - Generated secure key (32+ characters)
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `ALLOWED_ORIGINS` - Your domain(s) for CORS (or `*` for testing)

## AWS Setup

- [ ] RDS PostgreSQL database created
- [ ] Database security group configured
- [ ] Database endpoint and credentials noted
- [ ] Domain registered (optional)
- [ ] SSL certificate requested (if using domain)

## Deployment Steps

1. [ ] Install AWS CLI and configure
2. [ ] Install EB CLI: `pip install awsebcli`
3. [ ] Initialize EB: `eb init`
4. [ ] Create environment with env vars
5. [ ] Deploy: `eb deploy`
6. [ ] Verify health: `eb health`
7. [ ] Test application: `eb open`

## Post-Deployment

- [ ] Application accessible via EB URL
- [ ] Health checks passing (`/health`, `/ready`)
- [ ] Can sign up and login
- [ ] Can create conversations
- [ ] Messages work via WebSocket
- [ ] Domain configured (if applicable)
- [ ] HTTPS working (if domain configured)
- [ ] Monitoring/alerts set up

## Security Checklist

- [ ] `SECRET_KEY` is set (not default)
- [ ] `ALLOWED_ORIGINS` is restricted (not `*`)
- [ ] Database is not publicly accessible (or restricted)
- [ ] Security groups properly configured
- [ ] SSL certificate installed (if using domain)
