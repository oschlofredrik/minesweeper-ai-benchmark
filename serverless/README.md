# Serverless Architecture for Tilts Platform

## Overview
This directory contains the serverless-first architecture for the Tilts AI Benchmark platform, designed for infinite scalability and minimal operational overhead.

## Architecture Components

### 1. Frontend (Vercel)
- **Directory**: `serverless/frontend`
- **Technology**: React + Vite
- **Deployment**: Vercel Edge Network
- **Features**:
  - Static site generation
  - Edge functions for API routes
  - Global CDN distribution
  - Automatic HTTPS

### 2. API (AWS Lambda)
- **Directory**: `serverless/api`
- **Technology**: Python FastAPI + Mangum
- **Deployment**: AWS Lambda + API Gateway
- **Features**:
  - Serverless REST API
  - Auto-scaling
  - Pay-per-request pricing

### 3. Workers (AWS Lambda)
- **Directory**: `serverless/workers`
- **Technology**: Python
- **Deployment**: AWS Lambda + SQS
- **Features**:
  - Background job processing
  - Model evaluation workers
  - Task generation

### 4. Shared Resources
- **Directory**: `serverless/shared`
- **Components**:
  - DynamoDB tables configuration
  - S3 bucket policies
  - IAM roles and policies
  - Shared utilities

## Deployment Commands

### Frontend (Vercel)
```bash
# Deploy to preview
./serverless/deploy-vercel.sh

# Deploy to production
./serverless/deploy-vercel.sh production
```

### API (AWS Lambda)
```bash
# Deploy API
./serverless/deploy-lambda.sh api

# Deploy Workers
./serverless/deploy-lambda.sh workers
```

### Infrastructure (Terraform)
```bash
cd serverless/infrastructure
terraform init
terraform plan
terraform apply
```

## Service URLs
- **Frontend**: https://tilts.vercel.app
- **API**: https://api.tilts.example.com
- **WebSocket**: wss://ws.tilts.example.com

## Environment Variables

### Vercel
- `VITE_API_URL`: API endpoint URL
- `VITE_WS_URL`: WebSocket endpoint URL

### AWS Lambda
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `DYNAMODB_TABLE_PREFIX`: DynamoDB table prefix
- `S3_BUCKET_NAME`: S3 bucket for game data

## Cost Optimization
- Frontend: Free tier covers most usage
- API: Lambda free tier = 1M requests/month
- Database: DynamoDB on-demand pricing
- Storage: S3 standard for active data, Glacier for archives

## Monitoring
- Vercel Analytics for frontend
- AWS CloudWatch for Lambda functions
- Custom dashboards for game metrics