#!/bin/bash
# Quick debug script for common Vercel deployment issues

echo "🚀 Tilts Platform Quick Debug"
echo "============================"
echo ""

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 not found. Please install it first."
        return 1
    fi
    return 0
}

# Check prerequisites
echo "Checking prerequisites..."
check_command "vercel" || exit 1
check_command "curl" || exit 1
check_command "jq" || exit 1

# Get deployment info
echo -e "\n📍 Deployment Info:"
DEPLOYMENT_JSON=$(vercel list --json --count 1 2>/dev/null)
if [ $? -eq 0 ]; then
    DEPLOYMENT_URL=$(echo $DEPLOYMENT_JSON | jq -r '.[0].url')
    DEPLOYMENT_STATE=$(echo $DEPLOYMENT_JSON | jq -r '.[0].state')
    DEPLOYMENT_CREATED=$(echo $DEPLOYMENT_JSON | jq -r '.[0].created')
    
    echo "URL: https://$DEPLOYMENT_URL"
    echo "State: $DEPLOYMENT_STATE"
    echo "Created: $(date -d @$((DEPLOYMENT_CREATED/1000)) 2>/dev/null || date -r $((DEPLOYMENT_CREATED/1000)) 2>/dev/null || echo $DEPLOYMENT_CREATED)"
else
    echo "❌ Could not get deployment info"
fi

# Check environment variables
echo -e "\n🔑 Environment Variables:"
vercel env list | grep -E "(OPENAI|ANTHROPIC|SUPABASE)" | while read line; do
    VAR_NAME=$(echo $line | awk '{print $1}')
    echo "✅ $VAR_NAME is set"
done

# Quick health check
if [ ! -z "$DEPLOYMENT_URL" ]; then
    echo -e "\n🏥 Health Check:"
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL/health")
    if [ "$HEALTH_STATUS" = "200" ]; then
        echo "✅ Health endpoint: OK"
    else
        echo "❌ Health endpoint: $HEALTH_STATUS"
    fi
    
    # Check key endpoints
    echo -e "\n🔍 API Endpoints:"
    endpoints=(
        "/api/models"
        "/api/leaderboard"
        "/api/sessions"
    )
    
    for endpoint in "${endpoints[@]}"; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL$endpoint")
        if [ "$STATUS" = "200" ]; then
            echo "✅ $endpoint: OK"
        else
            echo "❌ $endpoint: $STATUS"
        fi
    done
fi

# Check recent errors
echo -e "\n⚠️  Recent Errors (last 10 minutes):"
ERROR_COUNT=$(vercel logs --since 10m --search "ERROR" 2>/dev/null | wc -l)
if [ $ERROR_COUNT -gt 0 ]; then
    echo "Found $ERROR_COUNT error(s)"
    echo "Run 'vercel logs --since 10m --search ERROR' to see details"
else
    echo "✅ No errors in last 10 minutes"
fi

# Common issues check
echo -e "\n📋 Common Issues Check:"

# Check for module import errors
MODULE_ERRORS=$(vercel logs --since 1h --search "No module named" 2>/dev/null | head -5)
if [ ! -z "$MODULE_ERRORS" ]; then
    echo "❌ Module import errors found:"
    echo "$MODULE_ERRORS" | head -3
else
    echo "✅ No module import errors"
fi

# Check for API key errors
API_ERRORS=$(vercel logs --since 1h --search "API key" 2>/dev/null | head -5)
if [ ! -z "$API_ERRORS" ]; then
    echo "❌ API key errors found"
else
    echo "✅ No API key errors"
fi

# Suggestions
echo -e "\n💡 Quick Actions:"
echo "1. View live logs: vercel logs --follow"
echo "2. Test locally: vercel dev"
echo "3. Run full diagnostic: python scripts/debug-vercel.py"
echo "4. Monitor functions: ./scripts/monitor-functions.sh"
echo "5. Test AI endpoints: python scripts/test-ai-endpoints.py"

echo -e "\n✨ Debug complete!"