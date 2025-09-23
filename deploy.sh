#!/bin/bash

# AWS Deployment Script for Website Chatbot
# This script deploys the frontend to AWS Amplify and backend to AWS App Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_success "All dependencies are installed."
}

# Check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "AWS credentials are configured."
}

# Deploy frontend to Amplify
deploy_frontend() {
    print_status "Deploying frontend to AWS Amplify..."
    
    cd frontend
    
    # Build the frontend
    print_status "Building frontend..."
    npm install
    npm run build
    
    # Deploy to Amplify (this would typically be done through Amplify console or CLI)
    print_warning "Frontend build completed. Please deploy manually to AWS Amplify:"
    print_warning "1. Go to AWS Amplify Console"
    print_warning "2. Connect your GitHub repository"
    print_warning "3. Use the amplify.yml configuration file"
    
    cd ..
}

# Build and push Docker image to ECR
build_and_push_docker() {
    print_status "Building and pushing Docker image to ECR..."
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    if [ -z "$AWS_REGION" ]; then
        AWS_REGION="us-east-1"
    fi
    
    ECR_REPOSITORY="zulfi-web-chatbot"
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
    
    # Create ECR repository if it doesn't exist
    print_status "Creating ECR repository if it doesn't exist..."
    aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    
    # Login to ECR
    print_status "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build and tag Docker image
    print_status "Building Docker image..."
    docker build -t $ECR_REPOSITORY .
    docker tag $ECR_REPOSITORY:latest $ECR_URI:latest
    
    # Push to ECR
    print_status "Pushing Docker image to ECR..."
    docker push $ECR_URI:latest
    
    print_success "Docker image pushed to ECR: $ECR_URI:latest"
}

# Deploy backend to App Runner
deploy_backend() {
    print_status "Deploying backend to AWS App Runner..."
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    if [ -z "$AWS_REGION" ]; then
        AWS_REGION="us-east-1"
    fi
    
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/zulfi-web-chatbot:latest"
    
    # Create App Runner service
    print_status "Creating App Runner service..."
    
    # Create the service configuration
    cat > apprunner-service.json << EOF
{
    "ServiceName": "zulfi-web-chatbot",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "$ECR_URI",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "IBM_API_KEY": "$IBM_API_KEY",
                    "WATSONX_PROJECT_ID": "$WATSONX_PROJECT_ID",
                    "WATSONX_URL": "https://ca-tor.ml.cloud.ibm.com",
                    "WATSONX_MODEL_ID": "meta-llama/llama-3-3-70b-instruct",
                    "ASTRA_COLLECTION_NAME": "chatbot_chunks",
                    "ASTRA_KEYSPACE": "default_keyspace",
                    "EMBED_MODEL": "sentence-transformers/all-mpnet-base-v2",
                    "ASTRA_DEVOPS_TOKEN": "$ASTRA_DEVOPS_TOKEN",
                    "ASTRA_REGION": "us-east-2",
                    "ASTRA_CLOUD": "AWS",
                    "ASTRA_TIER": "serverless",
                    "ASTRA_DB_TYPE": "vector",
                    "ASTRA_ORG_ID": "d246feda-e91c-4e62-a0c3-6bc647450366",
                    "ASTRA_DB_API_ENDPOINT": "https://8041aeca-643a-4117-a4d3-092a4ef12b81-us-east-2.apps.astra.datastax.com",
                    "ASTRA_DB_APPLICATION_TOKEN": "$ASTRA_DB_APPLICATION_TOKEN"
                }
            }
        },
        "AutoDeploymentsEnabled": false
    },
    "InstanceConfiguration": {
        "Cpu": "1024",
        "Memory": "2048"
    }
}
EOF
    
    # Create the App Runner service
    aws apprunner create-service --cli-input-json file://apprunner-service.json --region $AWS_REGION
    
    print_success "App Runner service created successfully!"
    print_warning "Note: It may take several minutes for the service to be ready."
    
    # Clean up
    rm apprunner-service.json
}

# Main deployment function
main() {
    print_status "Starting AWS deployment..."
    
    check_dependencies
    check_aws_credentials
    
    # Check if environment variables are set
    if [ -z "$IBM_API_KEY" ] || [ -z "$WATSONX_PROJECT_ID" ] || [ -z "$ASTRA_DEVOPS_TOKEN" ] || [ -z "$ASTRA_DB_APPLICATION_TOKEN" ]; then
        print_error "Required environment variables are not set:"
        print_error "Please set: IBM_API_KEY, WATSONX_PROJECT_ID, ASTRA_DEVOPS_TOKEN, ASTRA_DB_APPLICATION_TOKEN"
        exit 1
    fi
    
    build_and_push_docker
    deploy_backend
    deploy_frontend
    
    print_success "Deployment completed!"
    print_status "Check AWS App Runner console for the backend service URL"
    print_status "Check AWS Amplify console for the frontend URL"
}

# Run main function
main "$@"