#!/bin/bash

# Tilts Serverless CLI - Main management interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║       Tilts Serverless CLI           ║"
echo "║   Manage your serverless platform    ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Help function
show_help() {
    echo "Usage: ./tilts-cli.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  setup         - Initial setup of all services"
    echo "  deploy        - Deploy a service"
    echo "  status        - Check deployment status"
    echo "  logs          - View service logs"
    echo "  test          - Run tests"
    echo "  destroy       - Tear down infrastructure"
    echo ""
    echo "Options:"
    echo "  --service     - Service name (frontend|api|workers|all)"
    echo "  --stage       - Deployment stage (dev|staging|production)"
    echo ""
    echo "Examples:"
    echo "  ./tilts-cli.sh deploy --service frontend --stage production"
    echo "  ./tilts-cli.sh logs --service api"
    echo "  ./tilts-cli.sh status"
}

# Parse arguments
COMMAND=$1
shift

SERVICE=""
STAGE="dev"

while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --stage)
            STAGE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Execute commands
case $COMMAND in
    setup)
        echo -e "${GREEN}Setting up Tilts Serverless Platform...${NC}"
        ./setup-serverless.sh
        ;;
        
    deploy)
        if [ -z "$SERVICE" ]; then
            echo -e "${RED}Error: --service is required${NC}"
            show_help
            exit 1
        fi
        
        echo -e "${GREEN}Deploying $SERVICE (stage: $STAGE)...${NC}"
        
        case $SERVICE in
            frontend)
                ./deploy-vercel.sh $STAGE
                ;;
            api)
                ./deploy-lambda.sh api $STAGE
                ;;
            workers)
                ./deploy-lambda.sh workers $STAGE
                ;;
            all)
                echo -e "${BLUE}Deploying all services...${NC}"
                ./deploy-vercel.sh $STAGE
                ./deploy-lambda.sh api $STAGE
                ./deploy-lambda.sh workers $STAGE
                ;;
            *)
                echo -e "${RED}Unknown service: $SERVICE${NC}"
                exit 1
                ;;
        esac
        ;;
        
    status)
        echo -e "${GREEN}Checking deployment status...${NC}"
        echo ""
        
        # Check Vercel
        echo -e "${BLUE}Frontend (Vercel):${NC}"
        if command -v vercel &> /dev/null; then
            cd frontend && vercel ls --no-color 2>/dev/null | head -5 || echo "No deployments found"
            cd ..
        else
            echo "Vercel CLI not installed"
        fi
        echo ""
        
        # Check AWS Lambda
        echo -e "${BLUE}API/Workers (AWS Lambda):${NC}"
        if command -v serverless &> /dev/null; then
            if [ -d "api" ]; then
                cd api && serverless info --stage $STAGE 2>/dev/null | grep -E "(service:|stage:|region:|endpoints:)" || echo "API not deployed"
                cd ..
            fi
        else
            echo "Serverless Framework not installed"
        fi
        ;;
        
    logs)
        if [ -z "$SERVICE" ]; then
            echo -e "${RED}Error: --service is required${NC}"
            show_help
            exit 1
        fi
        
        echo -e "${GREEN}Viewing logs for $SERVICE...${NC}"
        
        case $SERVICE in
            frontend)
                echo "Opening Vercel dashboard..."
                open "https://vercel.com/dashboard"
                ;;
            api|workers)
                cd $SERVICE
                serverless logs -f ${SERVICE} --stage $STAGE --tail
                ;;
            *)
                echo -e "${RED}Unknown service: $SERVICE${NC}"
                exit 1
                ;;
        esac
        ;;
        
    test)
        echo -e "${GREEN}Running tests...${NC}"
        
        # Frontend tests
        if [ -d "frontend/node_modules" ]; then
            echo -e "${BLUE}Frontend tests:${NC}"
            cd frontend && npm test
            cd ..
        fi
        
        # API tests
        if [ -d "api/tests" ]; then
            echo -e "${BLUE}API tests:${NC}"
            cd api && python -m pytest tests/
            cd ..
        fi
        ;;
        
    destroy)
        echo -e "${YELLOW}WARNING: This will destroy all infrastructure!${NC}"
        read -p "Are you sure? (yes/no) " -r
        if [[ $REPLY == "yes" ]]; then
            echo -e "${RED}Destroying infrastructure...${NC}"
            cd infrastructure
            terraform destroy
            cd ..
        else
            echo "Cancelled"
        fi
        ;;
        
    *)
        show_help
        ;;
esac