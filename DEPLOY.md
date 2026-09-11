# 🚀 DEPLOYMENT GUIDE

**Status**: ✅ Ready to Deploy  
**Estimated Time**: 15-20 minutes (full) or 5 minutes (quick)  
**Cost**: < $50/month  
**AWS Account**: 873363353263

---

## 🎯 Quick Reference

| Script | Purpose | Time | Use Case |
|--------|---------|------|----------|
| `./deploy.sh` | Full deployment with validation | 15-20 min | **First deployment or major changes** |
| `./deploy-quick.sh` | Git + Terraform only | 5 min | After `build_lambda.sh` already run |
| `./build_lambda.sh` | Build Lambda package only | 2 min | Dependency for both deploy scripts |
| `./test-backend.sh` | Comprehensive API testing | 3 min | Verify deployment success |
| `./rollback.sh` | Revert to previous state | 5 min | Emergency rollback |

---

## 📋 Prerequisites

- ✅ AWS CLI installed (`aws --version`)
- ✅ Terraform installed (`terraform --version`)
- ✅ Python 3.12+ (`python3 --version`)
- ✅ AWS credentials configured (`aws sts get-caller-identity`)
- ✅ Git configured (`git config --global user.email`)

---

## 🚀 Option 1: Full Deployment (Recommended)

**Best for**: First-time deployment or major infrastructure changes

```bash
cd /Users/mesonx/MY\ LAB/sQuark-flow

# Run full deployment with validation
./deploy.sh
```

**What it does**:
1. ✅ Validates environment (AWS, Git, Terraform)
2. ✅ Checks in changes to GitHub
3. ✅ Builds Lambda package
4. ✅ Deploys infrastructure with Terraform
5. ✅ Verifies deployment success
6. ✅ Shows integration guide

**Estimated Time**: 15-20 minutes

---

## ⚡ Option 2: Quick Deployment

**Best for**: Rapid deployments after initial setup

```bash
cd /Users/mesonx/MY\ LAB/sQuark-flow

# Prerequisites: ./build_lambda.sh must have already run
./deploy-quick.sh
```

**What it does**:
1. ✅ Git check-in and push
2. ✅ Terraform plan & apply
3. ✅ Health check

**Estimated Time**: 5 minutes

---

## 🔧 Manual Step-by-Step Deployment

**Best for**: Understanding each step or troubleshooting

### 1️⃣ Build Lambda Package (2 min)
```bash
cd /Users/mesonx/MY\ LAB/sQuark-flow
./build_lambda.sh
```
**Expected output**: `lambda_deployment.zip` (~8-10MB)

### 2️⃣ Check in changes to GitHub (1 min)
```bash
git add -A
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
```

### 3️⃣ Initialize Terraform (1 min)
```bash
cd terraform
terraform init
```
**Expected output**: `.terraform/` directory created

### 4️⃣ Plan Deployment (1 min)
```bash
terraform plan -out=tfplan
```
**Expected output**: Shows ~15 resources to be created

### 5️⃣ Deploy to AWS (5-10 min)
```bash
terraform apply tfplan
```
**Expected output**: All resources created successfully

### 6️⃣ Get Your API Endpoint (1 min)
```bash
terraform output -raw api_endpoint
# Save this! Example: https://abc123.execute-api.us-east-2.amazonaws.com/production
```

---

## ✅ Verify Deployment Success

### Health Check
```bash
API=$(terraform output -raw api_endpoint)
curl $API/health
# Expected: {"status": "healthy"}
```

### List Agents
```bash
curl $API/api/v1/agents | jq .
# Expected: Array of 9 agents
```

### List Models
```bash
curl $API/api/v1/agents/models/list | jq .
# Expected: Array of 4 models (gpt-4o, claude-3-opus, etc.)
```

### Run Full Test Suite
```bash
./test-backend.sh
```
**Runs**: 
- ✅ Health checks
- ✅ Agent/model enumeration
- ✅ Workflow CRUD operations
- ✅ Performance tests
- ✅ Error handling validation

---

## 🔄 Rollback Procedure

If something goes wrong, rollback to the previous state:

```bash
./rollback.sh
```

**What it does**:
1. ✅ Terraform destroy (removes AWS resources)
2. ✅ Git reset (reverts to previous commit)
3. ✅ Preserves local changes (soft reset)

**⚠️ Warning**: This destroys AWS resources. Use only if needed.

---

## 📊 Environment Variables

Create `.env` file for Terraform customization:

```bash
cat > terraform/terraform.tfvars << 'EOF'
aws_region    = "us-east-2"
environment   = "production"
app_name      = "unified-backend"
lambda_memory = 512
lambda_timeout = 30

# Upstash Redis (from myfamilyassistant)
upstash_redis_url = "https://..."
upstash_redis_token = "..."

# CORS Origins for your projects
cors_origins = [
  "http://localhost:3000",
  "https://myfamilyassistant.ai",
  "https://squark.ai"
]
EOF
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| `AWS credentials not found` | Run `aws login` or configure credentials |
| `Terraform not found` | Install Terraform: `brew install terraform` |
| `Lambda build fails` | Ensure Python 3.12 installed: `python3 --version` |
| `API not responding` | Check CloudWatch logs: `aws logs tail /aws/lambda/unified-backend --follow` |
| `CORS errors` | Update CORS origins in `terraform.tfvars` |

---

## 📈 Monitoring

### View Logs
```bash
aws logs tail /aws/lambda/unified-backend --follow
```

### View Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average
```

### CloudWatch Dashboard
```bash
API=$(terraform output -raw api_endpoint)
# Dashboard is included in Terraform - check AWS Console
aws cloudwatch list-dashboards
```

---

## 🎯 Next Steps

1. **Save your API endpoint**:
   ```bash
   export UNIFIED_BACKEND_URL=$(terraform output -raw api_endpoint)
   ```

2. **Integrate with projects**:
   - [MyFamilyAssistant.ai](./docs/INTEGRATE_MYFAMILY.md)
   - [sQuark.ai](./docs/INTEGRATE_SQUARK_AI.md)
   - [sQuark AI Browser](./docs/INTEGRATE_SQUARK_BROWSER.md)

3. **Add LLM API keys** (optional):
   - OpenAI API key for GPT models
   - Anthropic API key for Claude models

---

## 💰 Cost Management

Your deployment costs < $50/month:
- **Lambda**: ~$1/month (free tier + arm64 discount)
- **API Gateway**: ~$1/month
- **DynamoDB**: $20-25/month (on-demand)
- **CloudWatch**: $3-5/month
- **Upstash Redis**: $7/month

Monitor costs with:
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

---

## ✅ Verification

```bash
API=$(terraform output -raw api_endpoint)

# Test health
curl $API/health

# List agents
curl $API/api/v1/agents

# You're live! 🎉
```

---

## 📊 What Gets Deployed

| Component | Count | Status |
|-----------|-------|--------|
| Lambda Functions | 1 | ✅ |
| API Gateway | 1 | ✅ |
| DynamoDB Tables | 4 | ✅ |
| IAM Roles | 1 | ✅ |
| IAM Policies | 1 | ✅ |
| CloudWatch Logs | 2 | ✅ |
| CloudWatch Alarms | 2 | ✅ |
| **TOTAL** | **~15 resources** | ✅ |

---

## 💰 Estimated Monthly Cost

| Service | Cost |
|---------|------|
| Lambda | < $1 |
| API Gateway | < $1 |
| DynamoDB | $20-25 |
| CloudWatch | $3-5 |
| Redis | $7 |
| **TOTAL** | **< $50** ✅ |

---

## 🔗 Next Steps

1. **Save Your API Endpoint**
   ```bash
   terraform output -raw api_endpoint > api_endpoint.txt
   ```

2. **Integrate with Frontend**
   - See `docs/INTEGRATE_MYFAMILY.md` for myfamilyassistant
   - See `docs/INTEGRATE_SQUARK_AI.md` for sQuark.ai
   - See `docs/INTEGRATE_SQUARK.md` for sQuark Web

3. **Monitor & Debug**
   ```bash
   # View logs
   aws logs tail /aws/lambda/unified-agentic-backend-api --follow
   
   # Check status
   aws lambda get-function --function-name unified-agentic-backend-api
   ```

4. **Destroy (if needed)**
   ```bash
   cd terraform
   terraform destroy
   ```

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| `build_lambda.sh: permission denied` | Run: `chmod +x build_lambda.sh` |
| `terraform: command not found` | Install Terraform: `brew install terraform` |
| `AWS credentials not found` | Run: `aws configure` |
| `terraform init` fails | Check internet connection & AWS credentials |
| `terraform apply` fails | Check error message, usually permission related |
| `Lambda timeout` | Increase timeout in `terraform.tfvars` |
| `CORS errors in frontend` | Update `cors_origins` in `terraform.tfvars` |

---

## 📞 Need Help?

1. **Check Logs**
   ```bash
   aws logs tail /aws/lambda/unified-agentic-backend-api --follow
   ```

2. **Review Full README**
   ```bash
   open README.md
   ```

3. **Check Integration Guides**
   ```bash
   open docs/INTEGRATE_*.md
   ```

---

**You're ready! Deploy with confidence! 🚀**
