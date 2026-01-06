# Elastic Beanstalk Init Troubleshooting

## CodeCommit Error

### Problem
When running `eb init`, you get this error:
```
Do you wish to continue with CodeCommit? (Y/n): y
ERROR: ServiceError - User is not authorized to perform: codecommit:ListRepositories
```

### Solution

**Answer "n" (No) to CodeCommit!**

CodeCommit is **optional** and not required for deployment. You can:
- Use local git repository
- Deploy directly with `eb deploy`
- Use GitHub/GitLab for version control

### How to Fix

1. **If you already answered "y" and got the error:**
   - The init process may have partially completed
   - You can either:
     - **Option A**: Delete `.elasticbeanstalk/` and run `eb init` again, answering "n" to CodeCommit
     - **Option B**: Continue anyway - the config may still be usable

2. **Run `eb init` again:**
   ```bash
   # If needed, remove partial config
   rm -rf .elasticbeanstalk/

   # Run init again
   eb init
   ```

3. **When prompted:**
   - **CodeCommit**: Answer **"n" (No)**
   - Everything else: Answer as needed

### Alternative: Add CodeCommit Permissions (Not Recommended)

If you really want to use CodeCommit (not necessary), you would need to add these IAM permissions:
- `codecommit:CreateRepository`
- `codecommit:CreateBranch`
- `codecommit:GetRepository`
- `codecommit:ListRepositories`
- `codecommit:ListBranches`

But this is **not recommended** - just answer "n" to CodeCommit and use `eb deploy` instead.

## Other Common Issues

### Platform Version Selection

When asked to select a platform branch, choose:
- **Python 3.11 or 3.12** (recommended - most stable and well-supported)
- **Python 3.9** (if you need older compatibility)
- **Note**: Python 3.10 may not be available in all AWS regions or platform versions
- Avoid Python 3.13 or 3.14 if they're too new (may have compatibility issues)

**Available options typically include:**
- Python 3.14 (very new, may have issues)
- Python 3.13 (new, may have issues)
- Python 3.12 (recommended)
- Python 3.11 (recommended)
- Python 3.9 (stable, older)

**Recommendation**: Choose **Python 3.11** or **3.12** for the best balance of features and stability.

### SSH Keypair

- **Yes** to SSH (recommended for troubleshooting)
- **Create new keypair** if you don't have one
- Save the keypair name - you'll need it to SSH into instances

### Region Selection

- Choose the same region where you created your RDS database
- Common choices: `us-east-1`, `us-west-2`, `eu-west-1`

## After Successful Init

Once `eb init` completes successfully, you should have:
- `.elasticbeanstalk/config.yml` file
- Application created in AWS Elastic Beanstalk

Next steps:
1. Create environment: `eb create pneumatic-chat-prod`
2. Set environment variables: `eb setenv KEY=value`
3. Deploy: `eb deploy`
