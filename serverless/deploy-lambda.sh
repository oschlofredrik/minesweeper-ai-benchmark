#!/bin/bash

# Deploy Tilts API/Workers to AWS Lambda

set -e

SERVICE=$1
STAGE=${2:-dev}

if [ -z "$SERVICE" ]; then
    echo "Usage: ./deploy-lambda.sh [api|workers] [stage]"
    exit 1
fi

echo "🚀 Deploying Tilts $SERVICE to AWS Lambda (Stage: $STAGE)..."

# Check if Serverless Framework is installed
if ! command -v serverless &> /dev/null; then
    echo "❌ Serverless Framework not found. Installing..."
    npm install -g serverless
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

# Deploy based on service
case $SERVICE in
    "api")
        echo "📦 Deploying API..."
        cd serverless/api
        npm install
        serverless deploy --stage $STAGE
        ;;
    "workers")
        echo "📦 Deploying Workers..."
        cd serverless/workers
        npm install
        serverless deploy --stage $STAGE
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo "Available services: api, workers"
        exit 1
        ;;
esac

echo "✅ Deployment complete!"

# Get service info
serverless info --stage $STAGE