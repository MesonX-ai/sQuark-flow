# 🚀 DEPLOYMENT QUICK START

**Status**: ✅ Ready to Deploy  
**Estimated Time**: 5 minutes  
**Cost**: < $50/month  
**AWS Account**: 873363353263

---

## One-Liner Deployment

```bash
cd /Users/mesonx/MY\ LAB/unified-backend-complete && ./build_lambda.sh && cd terraform && terraform init && terraform plan && terraform apply
```

---

## Step-by-Step

### 1️⃣ Build Lambda Package (2 min)
```bash
cd /Users/mesonx/MY\ LAB/unified-backend-complete
./build_lambda.sh
```
**Expect**: `lambda_deployment.zip` created

### 2️⃣ Initialize Terraform (1 min)
```bash
cd terraform
terraform init
```
**Expect**: `.terraform/` directory created

### 3️⃣ Plan Deployment (1 min)
```bash
terraform plan -out=tfplan
```
**Expect**: Shows ~15 resources to be created

### 4️⃣ Deploy to AWS (3 min)
```bash
terraform apply tfplan
```
**Expect**: All resources created successfully

### 5️⃣ Get Your API Endpoint
```bash
terraform output api_endpoint
```
**Copy this URL** - you'll need it for frontend integration!

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
