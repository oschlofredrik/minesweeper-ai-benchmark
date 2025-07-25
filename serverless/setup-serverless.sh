#!/bin/bash

# Complete serverless setup for Tilts platform

set -e

echo "🚀 Setting up Serverless Architecture for Tilts Platform"
echo "================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Installing..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform first."
    echo "Visit: https://www.terraform.io/downloads"
    exit 1
fi

# Install global CLIs
echo "📦 Installing global CLIs..."
npm install -g vercel serverless

# Setup infrastructure
echo "🏗️  Setting up AWS infrastructure..."
cd serverless/infrastructure
terraform init
terraform plan -out=tfplan
read -p "Deploy infrastructure? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply tfplan
fi
cd ../..

# Setup Frontend
echo "🎨 Setting up Frontend..."
cd serverless/frontend
npm install
cd ../..

# Setup API
echo "🔧 Setting up API..."
cd serverless/api
npm init -y
npm install --save-dev serverless-python-requirements serverless-offline
cd ../..

# Create environment files
echo "🔐 Creating environment files..."

# Frontend .env
cat > serverless/frontend/.env <<EOF
VITE_API_URL=https://api.tilts.example.com
VITE_WS_URL=wss://ws.tilts.example.com
EOF

# API .env
cat > serverless/api/.env <<EOF
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
EOF

echo "✅ Serverless setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update API keys in serverless/api/.env"
echo "2. Deploy frontend: ./serverless/deploy-vercel.sh"
echo "3. Deploy API: ./serverless/deploy-lambda.sh api"
echo "4. Update frontend .env with actual API URLs"
echo ""
echo "📚 Documentation: serverless/README.md"