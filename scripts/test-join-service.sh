#!/bin/bash
# Test script for join service functionality

echo "🧪 Testing Tilts Join Service..."
echo "==============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service URLs
if [ "$1" == "prod" ]; then
    JOIN_URL="https://join.tilts.com"
    MAIN_URL="https://tilts.com"
    echo "Testing PRODUCTION environment"
elif [ "$1" == "render" ]; then
    JOIN_URL="https://tilts-join.onrender.com"
    MAIN_URL="https://minesweeper-ai-benchmark.onrender.com"
    echo "Testing RENDER environment"
else
    JOIN_URL="http://localhost:8001"
    MAIN_URL="http://localhost:8000"
    echo "Testing LOCAL environment"
fi

echo ""
echo "Join Service: $JOIN_URL"
echo "Main Platform: $MAIN_URL"
echo ""

# Test 1: Health Check
echo -n "1. Health Check... "
health_response=$(curl -s "$JOIN_URL/health" 2>/dev/null)
if echo "$health_response" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "   Response: $health_response"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "   Response: $health_response"
fi

# Test 2: Home Page
echo -n "2. Home Page... "
home_response=$(curl -s -o /dev/null -w "%{http_code}" "$JOIN_URL/" 2>/dev/null)
if [ "$home_response" == "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $home_response)"
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $home_response)"
fi

# Test 3: PIN Validation - Valid PIN
echo -n "3. PIN Validation (Valid)... "
pin_response=$(curl -s "$JOIN_URL/api/check/TEST123" 2>/dev/null)
if echo "$pin_response" | grep -q "valid"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "   Response: $pin_response"
else
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "   Response: $pin_response"
    echo "   Note: This may fail if main platform is not running"
fi

# Test 4: PIN Validation - Invalid PIN
echo -n "4. PIN Validation (Invalid)... "
invalid_response=$(curl -s "$JOIN_URL/api/check/ABC" 2>/dev/null)
if echo "$invalid_response" | grep -q "detail"; then
    echo -e "${GREEN}✓ PASSED${NC} (Correctly rejected short PIN)"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "   Response: $invalid_response"
fi

# Test 5: CORS Headers
echo -n "5. CORS Headers... "
cors_response=$(curl -s -I -X OPTIONS "$JOIN_URL/api/check/TEST" \
    -H "Origin: $MAIN_URL" \
    -H "Access-Control-Request-Method: GET" \
    2>/dev/null | grep -i "access-control-allow-origin")
if [ ! -z "$cors_response" ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "   $cors_response"
else
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "   CORS headers might not be properly configured"
fi

# Test 6: Main Platform Integration
if [ "$1" != "prod" ]; then  # Skip in production to avoid creating test data
    echo -n "6. Main Platform Integration... "
    platform_health=$(curl -s "$MAIN_URL/health" 2>/dev/null)
    if echo "$platform_health" | grep -q "healthy"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        echo "   Main platform is responding"
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        echo "   Main platform might not be running"
    fi
else
    echo "6. Main Platform Integration... ${YELLOW}SKIPPED${NC} (Production environment)"
fi

echo ""
echo "==============================="
echo "Test Summary Complete"
echo ""
echo "Next Steps:"
echo "1. If running locally, ensure both services are running:"
echo "   - ./scripts/start-join-service.sh"
echo "   - python -m src.cli.main serve"
echo ""
echo "2. For production deployment:"
echo "   - Deploy to Render using render-join.yaml"
echo "   - Configure custom domain in Render dashboard"
echo "   - Update DNS records for join.tilts.com"
echo ""