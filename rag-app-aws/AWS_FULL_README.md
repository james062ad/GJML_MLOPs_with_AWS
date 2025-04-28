# Complete AWS Migration Guide for RAG Application

This guide provides detailed, step-by-step instructions for migrating your RAG application to AWS. It's written specifically for beginners and assumes no prior AWS experience.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Database Migration](#database-migration)
5. [Container Migration](#container-migration)
6. [Application Configuration](#application-configuration)
7. [Deployment](#deployment)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:
- An AWS account (create one at [aws.amazon.com](https://aws.amazon.com))
- AWS CLI installed ([installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- Docker installed locally
- Basic understanding of:
  - Docker containers
  - PostgreSQL
  - Python
  - REST APIs

## AWS Account Setup

### 1. Create an AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the sign-up process
4. **Important**: Save your root user credentials securely

### 2. Create an IAM User
1. Go to IAM in AWS Console
2. Click "Users" → "Add user"
3. Name: `rag-admin`
4. Select "Access key - Programmatic access"
5. Click "Next: Permissions"
6. Attach these policies:
   - `AdministratorAccess` (for development)
   - `AmazonBedrockFullAccess`
7. Complete the process and save the access key and secret

### 3. Configure AWS CLI
```bash
aws configure
# Enter your access key and secret when prompted
# Enter your preferred region (e.g., us-east-1)
# Enter json as output format
```

## Infrastructure Setup

### 1. Create VPC
1. Go to VPC Dashboard
2. Click "Create VPC"
3. Configure:
   - Name: `rag-vpc`
   - IPv4 CIDR: `10.0.0.0/16`
   - Select "Create VPC and more"
   - Number of AZs: 2
   - Number of public subnets: 2
   - Number of private subnets: 2
   - Enable NAT Gateway
   - Enable VPC endpoints for S3 and DynamoDB

### 2. Create Security Groups
1. Go to EC2 → Security Groups
2. Create for each service:
   ```bash
   # Database Security Group
   aws ec2 create-security-group \
       --group-name rag-db-sg \
       --description "Security group for RAG database"
   
   # Application Security Group
   aws ec2 create-security-group \
       --group-name rag-app-sg \
       --description "Security group for RAG application"
   ```

3. Add rules:
   ```bash
   # Database rules
   aws ec2 authorize-security-group-ingress \
       --group-name rag-db-sg \
       --protocol tcp \
       --port 5432 \
       --source-group rag-app-sg
   
   # Application rules
   aws ec2 authorize-security-group-ingress \
       --group-name rag-app-sg \
       --protocol tcp \
       --port 80 \
       --cidr 0.0.0.0/0
   ```

## Database Migration

### 1. Create RDS Instance
1. Go to RDS Dashboard
2. Click "Create database"
3. Choose:
   - Standard create
   - PostgreSQL
   - Free tier eligible
   - DB instance identifier: `rag-db`
   - Master username: `postgres`
   - Master password: [create secure password]
   - Instance configuration: db.t3.micro
   - Storage: 20 GB
   - VPC: `rag-vpc`
   - Security group: `rag-db-sg`

### 2. Configure pgvector
1. Connect to database:
   ```bash
   psql -h [your-rds-endpoint] -U postgres
   ```
2. Install pgvector:
   ```sql
   CREATE EXTENSION vector;
   ```

### 3. Migrate Data
1. Export local data:
   ```bash
   pg_dump -U postgres -h localhost rag_db > rag_backup.sql
   ```
2. Import to RDS:
   ```bash
   psql -h [your-rds-endpoint] -U postgres -d rag_db < rag_backup.sql
   ```

## Container Migration

### 1. Create ECR Repositories
```bash
# Create repositories
aws ecr create-repository --repository-name rag-app
aws ecr create-repository --repository-name rag-embeddings
aws ecr create-repository --repository-name rag-generation

# Get login token
aws ecr get-login-password --region [your-region] | docker login --username AWS --password-stdin [your-account-id].dkr.ecr.[your-region].amazonaws.com
```

### 2. Build and Push Images
```bash
# Build images
docker build -t rag-app .
docker build -t rag-embeddings ./embeddings
docker build -t rag-generation ./generation

# Tag images
docker tag rag-app:latest [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-app:latest
docker tag rag-embeddings:latest [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-embeddings:latest
docker tag rag-generation:latest [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-generation:latest

# Push images
docker push [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-app:latest
docker push [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-embeddings:latest
docker push [your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-generation:latest
```

### 3. Create ECS Cluster
1. Go to ECS Dashboard
2. Click "Create Cluster"
3. Choose:
   - Name: `rag-cluster`
   - Infrastructure: AWS Fargate
   - VPC: `rag-vpc`

### 4. Create Task Definitions
1. Go to ECS → Task Definitions
2. Create for each service:
   ```json
   {
     "family": "rag-app",
     "networkMode": "awsvpc",
     "containerDefinitions": [
       {
         "name": "rag-app",
         "image": "[your-account-id].dkr.ecr.[your-region].amazonaws.com/rag-app:latest",
         "portMappings": [
           {
             "containerPort": 80,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DB_HOST",
             "value": "[your-rds-endpoint]"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/rag-app",
             "awslogs-region": "[your-region]",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ],
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512"
   }
   ```

### 5. Create Services
1. Go to ECS → Clusters → `rag-cluster`
2. Click "Create Service"
3. Configure for each service:
   - Launch type: FARGATE
   - Task Definition: [select appropriate task definition]
   - Service name: [service name]
   - Number of tasks: 1
   - VPC: `rag-vpc`
   - Subnets: [select private subnets]
   - Security groups: `rag-app-sg`

## Application Configuration

### 1. Update Environment Variables
Create a `.env` file for each service:
```bash
# Database
DB_HOST=[your-rds-endpoint]
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=[your-password]

# AWS Bedrock
AWS_REGION=[your-region]
BEDROCK_MODEL_ID=amazon.titan-text-express-v1
```

### 2. Configure Load Balancer
1. Go to EC2 → Load Balancers
2. Click "Create Load Balancer"
3. Choose:
   - Application Load Balancer
   - Name: `rag-alb`
   - Scheme: internet-facing
   - VPC: `rag-vpc`
   - Mappings: [select public subnets]
   - Security groups: `rag-app-sg`
   - Listeners: HTTP:80
   - Target groups: Create new
     - Name: `rag-tg`
     - Protocol: HTTP
     - Port: 80
     - Target type: IP
     - Health check path: /health

## Deployment

### 1. Create Deployment Script
Create `deploy.sh`:
```bash
#!/bin/bash

# Update task definitions
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update services
aws ecs update-service --cluster rag-cluster --service rag-app --force-new-deployment
aws ecs update-service --cluster rag-cluster --service rag-embeddings --force-new-deployment
aws ecs update-service --cluster rag-cluster --service rag-generation --force-new-deployment
```

### 2. Deploy Application
```bash
chmod +x deploy.sh
./deploy.sh
```

## Monitoring and Maintenance

### 1. Set Up CloudWatch
1. Go to CloudWatch Dashboard
2. Create log groups:
   ```bash
   aws logs create-log-group --log-group-name /ecs/rag-app
   aws logs create-log-group --log-group-name /ecs/rag-embeddings
   aws logs create-log-group --log-group-name /ecs/rag-generation
   ```

### 2. Create Alarms
1. Go to CloudWatch → Alarms
2. Create basic alarms:
   - CPU Utilization > 80%
   - Memory Utilization > 80%
   - Error Rate > 1%

### 3. Set Up Backup
1. Go to RDS → Automated backups
2. Configure:
   - Retention period: 7 days
   - Backup window: [choose low-traffic time]
   - Enable encryption

## Troubleshooting

### Common Issues and Solutions

1. **Database Connection Issues**
   ```bash
   # Check security group rules
   aws ec2 describe-security-groups --group-ids [security-group-id]
   
   # Test connection
   psql -h [your-rds-endpoint] -U postgres -d rag_db
   ```

2. **Container Issues**
   ```bash
   # Check container logs
   aws logs get-log-events --log-group-name /ecs/rag-app --log-stream-name [stream-name]
   
   # Check task status
   aws ecs describe-tasks --cluster rag-cluster --tasks [task-id]
   ```

3. **Load Balancer Issues**
   ```bash
   # Check target health
   aws elbv2 describe-target-health --target-group-arn [target-group-arn]
   
   # Check security group rules
   aws ec2 describe-security-groups --group-ids [security-group-id]
   ```

### Getting Help
- AWS Support: [support.aws.amazon.com](https://support.aws.amazon.com)
- AWS Documentation: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- AWS Forums: [forums.aws.amazon.com](https://forums.aws.amazon.com)

## Cost Management

### 1. Set Up Budget Alerts
1. Go to AWS Billing → Budgets
2. Create budget:
   - Name: `rag-budget`
   - Budget amount: [your budget]
   - Alert threshold: 80%

### 2. Cost Optimization Tips
- Use AWS Free Tier where possible
- Use Spot Instances for non-critical workloads
- Set up auto-scaling based on demand
- Monitor and clean up unused resources

## Security Best Practices

1. **IAM**
   - Use IAM roles instead of access keys
   - Follow principle of least privilege
   - Regularly rotate credentials

2. **Network Security**
   - Use private subnets for sensitive resources
   - Implement security groups with minimal access
   - Enable VPC Flow Logs

3. **Data Security**
   - Enable encryption at rest
   - Use SSL/TLS for data in transit
   - Regular security audits

## Next Steps

### 1. Set up CI/CD Pipeline
1. Create GitHub repository for your code
2. Set up AWS CodePipeline:
   ```bash
   # Create pipeline
   aws codepipeline create-pipeline --cli-input-json file://pipeline.json
   ```
3. Configure GitHub webhooks
4. Set up build and test automation
5. Configure deployment stages

### 2. Implement Auto-scaling
1. Create Auto Scaling Group:
   ```bash
   aws autoscaling create-auto-scaling-group \
       --auto-scaling-group-name rag-asg \
       --min-size 1 \
       --max-size 5 \
       --desired-capacity 2
   ```
2. Set up scaling policies
3. Configure CloudWatch alarms
4. Test auto-scaling triggers

### 3. Set up Disaster Recovery
1. Create backup strategy:
   - Daily database backups
   - Weekly full system backups
   - Cross-region replication
2. Set up recovery procedures
3. Document recovery steps
4. Test recovery process

### 4. Implement Monitoring and Alerting
1. Set up CloudWatch dashboards
2. Configure alerts for:
   - System health
   - Performance metrics
   - Cost thresholds
   - Security events
3. Set up notification channels
4. Create incident response procedures

### 5. Regular Security Audits
1. Schedule monthly security reviews
2. Set up automated security scanning
3. Monitor compliance requirements
4. Update security policies

### 6. Cost Optimization
1. Review resource utilization
2. Implement cost-saving measures
3. Set up cost allocation tags
4. Monitor and adjust resources

## Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/) 