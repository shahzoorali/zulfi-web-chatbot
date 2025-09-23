# 🚀 AWS Quick Start Guide

## Overview
Your chatbot application is now ready for AWS deployment with:
- **Frontend**: React app deployed on AWS Amplify
- **Backend**: FastAPI server deployed on AWS App Runner

## 📋 Prerequisites
- AWS CLI installed and configured (`aws configure`)
- Docker installed (for App Runner deployment)
- Git repository (GitHub, GitLab, or Bitbucket)

## 🎯 Quick Deployment Options

### Option 1: Automated Script (Recommended)
```bash
./deploy.sh
```
Follow the interactive prompts to deploy your backend to App Runner.

### Option 2: Manual Deployment

#### Backend (AWS App Runner)
1. **Using Configuration File:**
   - Push code to Git repository
   - Go to AWS App Runner console
   - Create service from source code
   - Use `apprunner.yaml` configuration

2. **Using Docker:**
   - Build: `docker build -t chatbot-backend .`
   - Push to ECR (see deploy.sh for details)
   - Create App Runner service from ECR image

#### Frontend (AWS Amplify)
1. Go to AWS Amplify console
2. Connect your Git repository
3. Amplify will detect `amplify.yml` automatically
4. Update environment variables:
   - `VITE_API_BASE`: Your App Runner service URL
5. Deploy!

## 🔧 Configuration Files Created

| File | Purpose |
|------|---------|
| `apprunner.yaml` | App Runner service configuration |
| `frontend/amplify.yml` | Amplify build configuration |
| `Dockerfile` | Docker container for App Runner |
| `deploy.sh` | Automated deployment script |
| `.gitignore` | Exclude sensitive files from Git |

## 🌐 Expected URLs
- **Backend**: `https://[service-id].[region].awsapprunner.com`
- **Frontend**: `https://[app-id].amplifyapp.com`

## 🔐 Security Notes
- Environment variables are configured in deployment files
- Consider using AWS Secrets Manager for production
- CORS is configured for AWS domains

## 📊 Monitoring
- App Runner logs: AWS CloudWatch
- Amplify logs: Amplify console
- Metrics: CloudWatch dashboards

## 💰 Cost Estimation
- **App Runner**: ~$0.007/hour (scales to zero)
- **Amplify**: ~$0.01 per build + hosting
- **Free Tier**: Available for both services

## 🆘 Troubleshooting
1. **CORS Issues**: Update CORS origins in `server.py`
2. **Environment Variables**: Check App Runner/Amplify console
3. **Build Failures**: Check CloudWatch logs
4. **API Connection**: Verify App Runner service URL in frontend config

## 📚 Next Steps
1. Deploy backend using `./deploy.sh`
2. Deploy frontend via Amplify console
3. Update CORS settings with actual domain
4. Test the deployed application
5. Set up monitoring and alerts
