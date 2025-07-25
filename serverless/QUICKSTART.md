# Tilts Serverless Platform - Quick Start Guide

## Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **AWS Account** - [Sign up](https://aws.amazon.com/)
3. **Vercel Account** - [Sign up](https://vercel.com/)
4. **Terraform** - [Download](https://www.terraform.io/downloads)

## 1. Initial Setup

```bash
cd serverless
./tilts-cli.sh setup
```

This will:
- Install required CLIs (Vercel, Serverless Framework)
- Initialize Terraform
- Create environment files
- Install dependencies

## 2. Configure API Keys

Edit `serverless/api/.env`:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 3. Deploy Infrastructure

```bash
cd infrastructure
terraform apply
cd ..
```

## 4. Deploy Services

### Deploy Everything
```bash
./tilts-cli.sh deploy --service all --stage production
```

### Deploy Individual Services
```bash
# Frontend
./tilts-cli.sh deploy --service frontend --stage production

# API
./tilts-cli.sh deploy --service api --stage production

# Workers
./tilts-cli.sh deploy --service workers --stage production
```

## 5. Verify Deployment

```bash
./tilts-cli.sh status
```

## 6. View Logs

```bash
# Frontend logs (opens browser)
./tilts-cli.sh logs --service frontend

# API logs (streaming)
./tilts-cli.sh logs --service api
```

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │     │  API Gateway │     │     SQS     │
│  (Frontend) │────▶│   + Lambda   │────▶│  + Lambda   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  DynamoDB   │     │     S3      │
                    │  (Results)  │     │   (Games)   │
                    └─────────────┘     └─────────────┘
```

## Cost Estimates (Monthly)

- **Frontend (Vercel)**: Free tier covers most usage
- **API (Lambda)**: ~$0-5 for moderate usage
- **Database (DynamoDB)**: ~$0-10 on-demand
- **Storage (S3)**: ~$0-5 for game data
- **Total**: ~$0-25/month for typical usage

## Troubleshooting

### Vercel Deploy Fails
```bash
# Check Vercel login
vercel whoami

# Re-authenticate
vercel login
```

### Lambda Deploy Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Configure AWS
aws configure
```

### Terraform Issues
```bash
# Reinitialize
cd infrastructure
terraform init -upgrade
```

## Support

- GitHub Issues: Report bugs
- Vercel Support: Frontend issues
- AWS Support: Backend issues