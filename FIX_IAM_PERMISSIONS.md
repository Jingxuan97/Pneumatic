# Fix IAM Permissions for Elastic Beanstalk

## Problem
You're getting this error:
```
NotAuthorizedError - Operation Denied. User: arn:aws:iam::531901749923:user/cli-user
is not authorized to perform: elasticbeanstalk:CreateApplication
```

This means your IAM user `cli-user` doesn't have the necessary permissions to use Elastic Beanstalk.

## Solution: Add IAM Permissions

### Option 1: Use AWS Managed Policy (Easiest)

1. **Go to AWS Console** → IAM → Users → `cli-user`

2. **Click "Add permissions"** → "Attach policies directly"

3. **Search for and select:**
   - `AWSElasticBeanstalkFullAccess` (for full access)
   - OR `AWSElasticBeanstalkWebTier` + `AWSElasticBeanstalkWorkerTier` (for limited access)

4. **Also add these for RDS and other services:**
   - `AmazonRDSFullAccess` (if you need to create/manage RDS databases)
   - `AmazonEC2FullAccess` (Elastic Beanstalk uses EC2)
   - `AmazonS3FullAccess` (Elastic Beanstalk uses S3 for storage)
   - `IAMFullAccess` (if you need to create IAM roles)

5. **Click "Add permissions"**

### Option 2: Create Custom Policy (More Secure)

1. **Go to AWS Console** → IAM → Policies → "Create policy"

2. **Click "JSON" tab** and paste this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticbeanstalk:*",
                "ec2:*",
                "ec2:Describe*",
                "elasticloadbalancing:*",
                "autoscaling:*",
                "cloudwatch:*",
                "s3:*",
                "sns:*",
                "cloudformation:*",
                "iam:PassRole",
                "iam:GetRole",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:*"
            ],
            "Resource": "*"
        }
    ]
}
```

3. **Click "Next"** → Name it `ElasticBeanstalkDeploymentPolicy`

4. **Click "Create policy"**

5. **Go back to Users** → `cli-user` → "Add permissions" → "Attach policies directly"

6. **Search for and select** `ElasticBeanstalkDeploymentPolicy`

7. **Click "Add permissions"**

### Option 3: Use Administrator Access (For Testing Only)

⚠️ **Warning:** Only use this for development/testing. Not recommended for production.

1. **Go to AWS Console** → IAM → Users → `cli-user`

2. **Click "Add permissions"** → "Attach policies directly"

3. **Search for and select:** `AdministratorAccess`

4. **Click "Add permissions"**

## Minimum Required Permissions

For Elastic Beanstalk deployment, you need permissions for:

- **Elastic Beanstalk**: Create/update/delete applications and environments
- **EC2**: Launch and manage instances
- **S3**: Store application versions
- **CloudFormation**: Create stacks
- **IAM**: Create and manage roles (for EC2 instances)
- **RDS**: If you're creating/managing databases
- **VPC**: Network configuration (if using custom VPC)

## Verify Permissions

After adding permissions, wait 1-2 minutes for them to propagate, then test:

```bash
aws elasticbeanstalk describe-applications
```

If this works without errors, try `eb init` again.

## Troubleshooting

### Still Getting Permission Errors?

1. **Wait a few minutes** - IAM changes can take 1-2 minutes to propagate

2. **Check your IAM user:**
   ```bash
   aws sts get-caller-identity
   ```
   Should show your user ARN

3. **Test specific permission:**
   ```bash
   aws elasticbeanstalk describe-applications
   ```

4. **Check if you have multiple AWS profiles:**
   ```bash
   aws configure list-profiles
   ```
   Make sure you're using the right profile

5. **If using a profile, specify it:**
   ```bash
   eb init --profile default
   ```

### Common Issues

- **Permissions not propagated**: Wait 1-2 minutes after adding permissions
- **Wrong IAM user**: Make sure you're using the correct AWS credentials
- **Region restrictions**: Some permissions might be region-specific
- **Service limits**: Check if you've hit AWS service limits
