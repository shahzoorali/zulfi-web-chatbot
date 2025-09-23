# AWS Deployment Guide

This guide covers deploying the chatbot application to AWS using Amplify (frontend) and App Runner (backend).

## Prerequisites

1. AWS CLI installed and configured
2. AWS account with appropriate permissions
3. Git repository for the code

## Backend Deployment with AWS App Runner

### Option 1: Using App Runner Configuration File

1. **Push your code to a Git repository** (GitHub, GitLab, or Bitbucket)

2. **Create App Runner Service:**
   - Go to AWS App Runner console
   - Click "Create service"
   - Choose "Source code repository"
   - Connect your repository
   - Select the repository and branch
   - Choose "Use a configuration file" and specify `apprunner.yaml`
   - Review and create the service

### Option 2: Using Docker Container

1. **Build and push Docker image:**
   ```bash
   # Build the Docker image
   docker build -t chatbot-backend .
   
   # Tag for ECR (replace with your account ID and region)
   docker tag chatbot-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/chatbot-backend:latest
   
   # Push to ECR
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/chatbot-backend:latest
   ```

2. **Create App Runner Service from ECR:**
   - Go to AWS App Runner console
   - Choose "Container image"
   - Specify your ECR image URI
   - Configure port 8000
   - Add environment variables (see apprunner.yaml for reference)

## Frontend Deployment with AWS Amplify

1. **Connect Repository:**
   - Go to AWS Amplify console
   - Click "New app" > "Host web app"
   - Connect your Git provider
   - Select repository and branch

2. **Configure Build Settings:**
   - Amplify will detect the `amplify.yml` file automatically
   - Update the `VITE_API_BASE` environment variable with your App Runner service URL
   - The URL format will be: `https://[service-id].[region].awsapprunner.com`

3. **Deploy:**
   - Click "Save and deploy"
   - Amplify will build and deploy your frontend

## Environment Variables Configuration

### Backend (App Runner)
All environment variables are already configured in `apprunner.yaml`. For production, consider using AWS Secrets Manager for sensitive values.

### Frontend (Amplify)
Update the environment variables in Amplify console:
- `VITE_API_BASE`: Your App Runner service URL
- `VITE_API_KEY`: Optional API key for authentication
- `VITE_DEFAULT_RUN_ID`: Optional default run ID
- `VITE_TOP_K`: Number of results to return (default: 3)

## Post-Deployment Steps

1. **Update CORS Settings:**
   - Get your Amplify app URL
   - Update the CORS origins in `server.py` to include your Amplify domain
   - Redeploy the backend

2. **Test the Application:**
   - Visit your Amplify app URL
   - Test the chat functionality
   - Check browser console for any errors

## Monitoring and Logs

- **App Runner Logs:** Available in AWS CloudWatch
- **Amplify Logs:** Available in Amplify console build history
- **Performance:** Monitor through AWS CloudWatch metrics

## Security Considerations

1. **Environment Variables:** Use AWS Secrets Manager for sensitive data
2. **CORS:** Restrict origins to your actual domains
3. **API Authentication:** Consider implementing proper API authentication
4. **HTTPS:** Both services provide HTTPS by default

## Scaling

- **App Runner:** Auto-scales based on traffic
- **Amplify:** CDN distribution handles frontend scaling automatically

## Cost Optimization

- **App Runner:** Scales to zero when not in use
- **Amplify:** Pay per build minute and data transfer
- **Consider using AWS Free Tier** for initial testing

