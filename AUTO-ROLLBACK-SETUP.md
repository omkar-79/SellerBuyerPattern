# Automatic Rollback Setup Guide

This guide explains how to set up automatic rollback functionality for your Stock Market App using Render's API.

## 🚀 What is Automatic Rollback?

Automatic rollback monitors your deployed application and automatically reverts to the previous working version if:
- Health checks fail after deployment
- Service becomes unavailable
- Performance degrades significantly

## 🔧 Prerequisites

### 1. Render API Access
You need the following from your Render dashboard:

#### **Get Your Service ID:**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your service
3. Go to Settings → General
4. Copy the **Service ID** (format: `srv-xxxxxxxxxx`)

#### **Get Your API Key:**
1. Go to [Render Account Settings](https://dashboard.render.com/account)
2. Scroll to "API Keys" section
3. Click "Create API Key"
4. Give it a name (e.g., "Jenkins Auto Rollback")
5. Copy the generated API key

### 2. Jenkins Credentials Setup

Add these credentials to your Jenkins instance:

#### **RENDER_API_KEY:**
- **Type**: Secret text
- **ID**: `RENDER_API_KEY`
- **Secret**: Your Render API key

#### **RENDER_SERVICE_ID:**
- **Type**: Secret text  
- **ID**: `RENDER_SERVICE_ID`
- **Secret**: Your service ID (e.g., `srv-xxxxxxxxxx`)

#### **RENDER_DEPLOY_HOOK_PRODUCTION:**
- **Type**: Secret text
- **ID**: `RENDER_DEPLOY_HOOK_PRODUCTION`
- **Secret**: Your production deploy hook URL

## 📋 How It Works

### **Deployment Flow:**
1. **Deploy** → New version deployed to Render
2. **Wait** → 30 seconds for deployment to stabilize
3. **Health Check** → Test service health endpoint
4. **Monitor** → Up to 10 attempts over 100 seconds
5. **Decision** → Healthy = continue, Unhealthy = rollback
6. **Rollback** → Automatically revert to previous version
7. **Verify** → Confirm rollback was successful

### **Health Check Process:**
```bash
# Health check endpoint
GET https://your-app.onrender.com/_stcore/health

# Expected response: HTTP 200 OK
# If fails: Automatic rollback triggered
```

### **Rollback Process:**
```bash
# 1. Get deployment history
GET https://api.render.com/v1/services/{service_id}/deploys

# 2. Find previous successful deployment
# 3. Trigger rollback
POST https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/restore

# 4. Wait for rollback completion
# 5. Verify rollback health
```

## ⚙️ Configuration

### **Health Check Settings:**
- **Endpoint**: `/_stcore/health` (Streamlit health check)
- **Max Attempts**: 10 tries
- **Retry Interval**: 10 seconds between attempts
- **Timeout**: 10 seconds per request
- **Wait After Deploy**: 30 seconds

### **Rollback Settings:**
- **Trigger**: Health check failure
- **Action**: Rollback to previous deployment
- **Verification**: Confirm rollback health
- **Timeout**: 60 seconds for rollback completion

## 🔍 Monitoring & Logging

### **What Gets Logged:**
- ✅ Health check attempts and results
- 🔄 Rollback triggers and actions
- 📊 Deployment history and status
- ❌ Failure reasons and error messages

### **Jenkins Console Output:**
```
🔍 Performing health checks...
Service URL: https://your-app.onrender.com
Health check attempt 1/10...
✅ Health check passed on attempt 1
✅ Service is healthy - no rollback needed
```

**Or if rollback is needed:**
```
❌ Health check failed after 10 attempts
🔄 Initiating automatic rollback...
📋 Getting deployment history...
🔄 Rolling back to deployment: deploy-xxxxxxxxxx
⏳ Waiting for rollback to complete...
✅ Rollback successful - service is healthy
```

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. "No previous deployment found"**
**Cause**: This is the first deployment or no successful previous deployments
**Solution**: Manual intervention required - check Render dashboard

#### **2. "Rollback failed - service still unhealthy"**
**Cause**: Previous deployment also has issues
**Solution**: Manual intervention required - may need to rollback further

#### **3. "API authentication failed"**
**Cause**: Invalid API key or service ID
**Solution**: Verify credentials in Jenkins

#### **4. "Health check endpoint not responding"**
**Cause**: Service is down or endpoint changed
**Solution**: Check service status in Render dashboard

### **Manual Rollback (Fallback):**
If automatic rollback fails:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your service
3. Go to "Deploys" tab
4. Click "Rollback" on a previous successful deployment

## 📊 Rollback Scenarios

### **Scenario 1: New Code Has Bugs**
- **Trigger**: Health check fails after deployment
- **Action**: Automatic rollback to previous version
- **Result**: Service restored to working state

### **Scenario 2: Dependency Issues**
- **Trigger**: Service fails to start properly
- **Action**: Automatic rollback to previous version
- **Result**: Service restored with working dependencies

### **Scenario 3: Configuration Problems**
- **Trigger**: Service starts but health checks fail
- **Action**: Automatic rollback to previous version
- **Result**: Service restored with working configuration

## 🔧 Customization

### **Modify Health Check Endpoint:**
Edit `.rollback-config.yml`:
```yaml
health_check:
  endpoint: "/your-custom-health-endpoint"
```

### **Change Retry Settings:**
```yaml
health_check:
  max_attempts: 15
  retry_interval: 5
  timeout: 15
```

### **Add Custom Health Checks:**
```yaml
health_endpoints:
  primary: "/_stcore/health"
  secondary: "/api/status"
  custom: ["/health", "/ping"]
```

## 📈 Benefits

### **Automatic Rollback Provides:**
- ✅ **Faster Recovery**: No manual intervention needed
- ✅ **Reduced Downtime**: Quick rollback to working version
- ✅ **Better Reliability**: Automatic failure detection
- ✅ **Peace of Mind**: 24/7 monitoring and recovery
- ✅ **Consistent Process**: Same rollback logic every time

### **Business Impact:**
- **Reduced MTTR** (Mean Time To Recovery)
- **Improved User Experience** (less downtime)
- **Lower Operational Overhead** (less manual work)
- **Higher Confidence** in deployments

## 🎯 Best Practices

1. **Test Rollback Process**: Verify it works before relying on it
2. **Monitor Logs**: Check Jenkins console for rollback events
3. **Keep Deployments Small**: Easier to rollback smaller changes
4. **Document Changes**: Know what each deployment contains
5. **Have Backup Plans**: Manual rollback procedures as fallback

## 📞 Support

### **If Automatic Rollback Fails:**
1. Check Jenkins console logs
2. Verify Render API credentials
3. Check Render dashboard for service status
4. Use manual rollback as fallback
5. Contact DevOps team if issues persist

### **Getting Help:**
- Check `.rollback-config.yml` for configuration details
- Review Jenkins pipeline logs for error messages
- Consult Render API documentation
- Test health endpoints manually

---

**Your application now has automatic rollback protection! 🛡️**
