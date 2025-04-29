# AWS Bedrock Migration TODO List

> **Disclaimer**: This TODO list focuses on migrating only the LLM components (embeddings and generation) to AWS Bedrock while maintaining the current local container setup for the database and other services. This is a partial migration approach that keeps your existing infrastructure (PostgreSQL, containers) running locally while only moving the AI/ML components to AWS.
>
> For a complete step-by-step guide on migrating everything to AWS (including containers, database, and infrastructure), please refer to `AWS_FULL_README.md`. That guide is written specifically for beginners and includes detailed instructions for setting up the entire AWS infrastructure from scratch.
>
> **Note**: If you're new to AWS, we recommend starting with the full migration guide (`AWS_FULL_README.md`) as it provides a more structured and complete approach to cloud deployment.

## 1. AWS Infrastructure Setup
- [ ] Create AWS Bedrock access policy (already documented in README)
- [ ] Create IAM role with Bedrock permissions
- [ ] Enable required Bedrock models (Titan Text Embeddings V2, Titan G1 - Express)
- [ ] Set up AWS credentials and environment variables
- [ ] Configure AWS region settings

## 2. Embedding Service Migration
- [ ] Create new `bedrock_embeddings.py` service
- [ ] Implement Bedrock Titan Text Embeddings V2 client
- [ ] Update `embeddings.py` to use Bedrock embeddings
- [ ] Add error handling and retry logic for Bedrock API calls
- [ ] Update configuration to include Bedrock model settings
- [ ] Add embedding model version tracking

## 3. Generation Service Migration
- [ ] Create new `bedrock_generation.py` service
- [ ] Implement Bedrock Titan G1 - Express client
- [ ] Update `generation_service.py` to use Bedrock
- [ ] Modify prompt templates for Bedrock model
- [ ] Add response parsing and error handling
- [ ] Update configuration for Bedrock model parameters

## 4. Query Expansion Migration
- [ ] Update `query_expansion_service.py` to use Bedrock
- [ ] Modify expansion prompts for Bedrock model
- [ ] Add caching for expanded queries
- [ ] Implement fallback to OpenAI if needed

## 5. Configuration Updates
- [ ] Update `config.py` with Bedrock settings
- [ ] Add Bedrock model parameters to configuration
- [ ] Create environment variable templates
- [ ] Update deployment configurations

## 6. Testing and Validation
- [ ] Create test suite for Bedrock services
- [ ] Add integration tests for Bedrock API calls
- [ ] Implement performance benchmarking
- [ ] Add error scenario testing
- [ ] Create fallback mechanisms

## 7. Documentation
- [ ] Update API documentation
- [ ] Add Bedrock setup instructions
- [ ] Document model parameters and limitations
- [ ] Add troubleshooting guide
- [ ] Update deployment guide

## 8. Monitoring and Logging
- [ ] Add Bedrock API call monitoring
- [ ] Implement cost tracking
- [ ] Add performance metrics
- [ ] Set up error alerting
- [ ] Create usage dashboards

## 9. Security
- [ ] Implement AWS KMS for key management
- [ ] Add request signing
- [ ] Set up IAM role rotation
- [ ] Implement rate limiting
- [ ] Add security headers

## 10. Performance Optimization
- [ ] Implement request batching
- [ ] Add response caching
- [ ] Optimize prompt templates
- [ ] Add connection pooling
- [ ] Implement retry strategies

## 11. Deployment
- [ ] Update Docker configurations
- [ ] Modify deployment scripts
- [ ] Add Bedrock health checks
- [ ] Update CI/CD pipelines
- [ ] Create rollback procedures

## Next Steps

### 1. Set up CI/CD Pipeline
- [ ] Create GitHub repository for your code
- [ ] Set up AWS CodePipeline
- [ ] Configure GitHub webhooks
- [ ] Set up build and test automation
- [ ] Configure deployment stages

### 2. Implement Auto-scaling
- [ ] Create Auto Scaling Group
- [ ] Set up scaling policies
- [ ] Configure CloudWatch alarms
- [ ] Test auto-scaling triggers

### 3. Set up Disaster Recovery
- [ ] Create backup strategy
  - [ ] Daily database backups
  - [ ] Weekly full system backups
  - [ ] Cross-region replication
- [ ] Set up recovery procedures
- [ ] Document recovery steps
- [ ] Test recovery process

### 4. Implement Monitoring and Alerting
- [ ] Set up CloudWatch dashboards
- [ ] Configure alerts for:
  - [ ] System health
  - [ ] Performance metrics
  - [ ] Cost thresholds
  - [ ] Security events
- [ ] Set up notification channels
- [ ] Create incident response procedures

### 5. Regular Security Audits
- [ ] Schedule monthly security reviews
- [ ] Set up automated security scanning
- [ ] Monitor compliance requirements
- [ ] Update security policies

### 6. Cost Optimization
- [ ] Review resource utilization
- [ ] Implement cost-saving measures
- [ ] Set up cost allocation tags
- [ ] Monitor and adjust resources

## Notes
- Keep OpenAI as fallback during migration
- Implement gradual rollout strategy
- Monitor costs and usage patterns
- Consider implementing A/B testing
- Plan for maintenance windows 