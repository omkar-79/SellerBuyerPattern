# 🚀 Render.com Setup Guide for Stock Market Analysis App

## 📋 Overview

This guide will help you set up your Stock Market Analysis app on Render.com and integrate it with your Jenkins CI/CD pipeline.

## 🎯 Prerequisites

- Render.com account (free tier available)
- GitHub repository with your code
- Jenkins server with pipeline configured

## 🔧 Step 1: Create Render.com Services

### 1.1 Create Staging Service

1. **Go to Render.com Dashboard**
   - Visit [render.com](https://render.com)
   - Sign in to your account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure Staging Service**
   ```
   Name: stock-market-app-staging
   Environment: Python 3
   Region: Choose closest to your users
   Branch: develop
   Root Directory: (leave empty)
   Build Command: pip install -r requirements.txt
   Start Command: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
   ```

4. **Environment Variables**
   ```
   PYTHON_VERSION = 3.11.0
   STREAMLIT_SERVER_PORT = $PORT
   STREAMLIT_SERVER_ADDRESS = 0.0.0.0
   ```

5. **Advanced Settings**
   - **Auto-Deploy**: Disabled (we'll use Jenkins)
   - **Health Check Path**: `/_stcore/health`
   - **Plan**: Free (for staging)

### 1.2 Create Production Service

1. **Create Another Web Service**
   - Click "New +" → "Web Service"
   - Connect the same GitHub repository

2. **Configure Production Service**
   ```
   Name: stock-market-app-production
   Environment: Python 3
   Region: Choose closest to your users
   Branch: main
   Root Directory: (leave empty)
   Build Command: pip install -r requirements.txt
   Start Command: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Environment Variables**
   ```
   PYTHON_VERSION = 3.11.0
   STREAMLIT_SERVER_PORT = $PORT
   STREAMLIT_SERVER_ADDRESS = 0.0.0.0
   ```

4. **Advanced Settings**
   - **Auto-Deploy**: Disabled (we'll use Jenkins)
   - **Health Check Path**: `/_stcore/health`
   - **Plan**: Starter (recommended for production)

## 🔑 Step 2: Get Deploy Hook URLs

### 2.1 Staging Deploy Hook

1. **Go to Staging Service**
   - Click on your staging service
   - Go to "Settings" tab
   - Scroll down to "Deploy Hook"

2. **Copy Deploy Hook URL**
   ```
   https://api.render.com/deploy/srv-xxxxxxxxxx?key=your-staging-key
   ```

### 2.2 Production Deploy Hook

1. **Go to Production Service**
   - Click on your production service
   - Go to "Settings" tab
   - Scroll down to "Deploy Hook"

2. **Copy Deploy Hook URL**
   ```
   https://api.render.com/deploy/srv-yyyyyyyyyy?key=your-production-key
   ```

## 🔧 Step 3: Configure Jenkins

### 3.1 Add Credentials

1. **Go to Jenkins Dashboard**
   - Click "Manage Jenkins" → "Manage Credentials"
   - Click "System" → "Global credentials"
   - Click "Add Credentials"

2. **Add Staging Deploy Hook**
   ```
   Kind: Secret text
   Secret: https://api.render.com/deploy/srv-xxxxxxxxxx?key=your-staging-key
   ID: render-deploy-hook-staging
   Description: Render.com Staging Deploy Hook
   ```

3. **Add Production Deploy Hook**
   ```
   Kind: Secret text
   Secret: https://api.render.com/deploy/srv-yyyyyyyyyy?key=your-production-key
   ID: render-deploy-hook-production
   Description: Render.com Production Deploy Hook
   ```

### 3.2 Update Jenkinsfile

Your Jenkinsfile is already configured to use these credentials. The pipeline will:

1. **On `develop` branch push**:
   - Run tests and quality checks
   - Trigger staging deployment via deploy hook
   - Send Slack notification

2. **On `main` branch push**:
   - Run tests and quality checks
   - Ask for manual approval
   - Trigger production deployment via deploy hook
   - Send Slack notification

## 🧪 Step 4: Test the Pipeline

### 4.1 Test Staging Deployment

1. **Create a test branch**
   ```bash
   git checkout -b develop
   git push origin develop
   ```

2. **Monitor Jenkins Pipeline**
   - Go to Jenkins dashboard
   - Watch the pipeline execution
   - Check Render.com dashboard for deployment

3. **Verify Staging App**
   - Visit your staging URL: `https://stock-market-app-staging.onrender.com`
   - Test the application functionality

### 4.2 Test Production Deployment

1. **Merge to main**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

2. **Approve Production Deployment**
   - Jenkins will ask for manual approval
   - Click "Deploy" when ready

3. **Verify Production App**
   - Visit your production URL: `https://stock-market-app-production.onrender.com`
   - Test the application functionality

## 📊 Step 5: Monitor and Maintain

### 5.1 Render.com Monitoring

1. **Service Health**
   - Check service status in Render.com dashboard
   - Monitor logs for any issues
   - Set up alerts for downtime

2. **Performance Metrics**
   - Monitor response times
   - Check memory and CPU usage
   - Review deployment logs

### 5.2 Jenkins Monitoring

1. **Pipeline Status**
   - Monitor build success/failure rates
   - Check test coverage reports
   - Review security scan results

2. **Notifications**
   - Verify Slack notifications are working
   - Check email notifications for failures

## 🛠️ Troubleshooting

### Common Issues

1. **Deploy Hook Not Working**
   ```bash
   # Test deploy hook manually
   curl -X POST "YOUR_DEPLOY_HOOK_URL"
   
   # Check Render.com service logs
   # Go to service → Logs tab
   ```

2. **App Not Starting**
   ```bash
   # Check start command
   streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
   
   # Verify environment variables
   # Check Render.com service settings
   ```

3. **Build Failures**
   ```bash
   # Check build command
   pip install -r requirements.txt
   
   # Verify requirements.txt exists
   # Check Python version compatibility
   ```

### Debug Commands

```bash
# Test Streamlit locally
streamlit run main.py --server.port=8501

# Check dependencies
pip install -r requirements.txt

# Test deploy hook
curl -X POST "YOUR_DEPLOY_HOOK_URL"
```

## 📈 Performance Optimization

### Render.com Settings

1. **Free Plan Limitations**
   - 512MB RAM
   - 0.1 CPU
   - Sleeps after 15 minutes of inactivity

2. **Starter Plan Benefits**
   - 512MB RAM
   - 0.5 CPU
   - Always running
   - Custom domains

### Application Optimization

1. **Streamlit Configuration**
   ```python
   # Add to main.py
   st.set_page_config(
       page_title="Stock Market Analysis",
       layout="wide",
       initial_sidebar_state="expanded"
   )
   ```

2. **Caching**
   ```python
   @st.cache_data
   def fetch_stock_data(ticker):
       # Your data fetching logic
       pass
   ```

## 🔒 Security Considerations

1. **Environment Variables**
   - Never commit API keys to repository
   - Use Render.com environment variables
   - Rotate deploy hook keys regularly

2. **Access Control**
   - Limit who can trigger deployments
   - Use manual approval for production
   - Monitor deployment logs

## 📚 Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [Render.com Deploy Hooks](https://render.com/docs/deploy-hooks)
- [Streamlit on Render.com](https://docs.streamlit.io/streamlit-community-cloud)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)

---

**🎉 Your Stock Market Analysis App is now ready for automated deployment to Render.com!**
