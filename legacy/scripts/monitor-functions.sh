#!/bin/bash
# Real-time function monitoring for Vercel deployments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONITOR_DURATION=${1:-300}  # Default 5 minutes
ALERT_ON_ERROR=${2:-true}
LOG_FILE="monitor_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 Vercel Function Monitor"
echo "========================"
echo "Duration: ${MONITOR_DURATION} seconds"
echo "Log file: ${LOG_FILE}"
echo ""

# Check if vercel CLI is available
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found. Install with: npm i -g vercel${NC}"
    exit 1
fi

# Function to format log lines
format_log() {
    local line="$1"
    local timestamp=$(date +"%H:%M:%S")
    
    # Color code based on content
    if [[ $line == *"ERROR"* ]] || [[ $line == *"error"* ]]; then
        echo -e "${timestamp} ${RED}[ERROR]${NC} ${line}"
        echo "${timestamp} [ERROR] ${line}" >> "$LOG_FILE"
        
        # Alert on error if enabled
        if [ "$ALERT_ON_ERROR" = true ]; then
            echo -e "\a" # Terminal bell
        fi
    elif [[ $line == *"WARN"* ]] || [[ $line == *"warning"* ]]; then
        echo -e "${timestamp} ${YELLOW}[WARN]${NC} ${line}"
        echo "${timestamp} [WARN] ${line}" >> "$LOG_FILE"
    elif [[ $line == *"START"* ]] || [[ $line == *"INIT"* ]]; then
        echo -e "${timestamp} ${GREEN}[START]${NC} ${line}"
        echo "${timestamp} [START] ${line}" >> "$LOG_FILE"
    else
        echo "${timestamp} [INFO] ${line}"
        echo "${timestamp} [INFO] ${line}" >> "$LOG_FILE"
    fi
}

# Function to monitor specific endpoints
monitor_endpoints() {
    local endpoints=(
        "/api/benchmark/run"
        "/api/play"
        "/api/evaluate-sdk"
        "/api/competition-sdk"
    )
    
    echo -e "\n📊 Monitoring key endpoints..."
    for endpoint in "${endpoints[@]}"; do
        echo "   - $endpoint"
    done
    echo ""
}

# Get deployment URL
echo "Getting latest deployment..."
DEPLOYMENT_URL=$(vercel list --json --count 1 | jq -r '.[0].url' 2>/dev/null)

if [ -z "$DEPLOYMENT_URL" ]; then
    echo -e "${RED}❌ Could not get deployment URL${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Monitoring deployment:${NC} $DEPLOYMENT_URL"
echo ""

# Start monitoring
monitor_endpoints

echo "Starting log stream..."
echo "Press Ctrl+C to stop"
echo "================================"

# Use timeout to limit monitoring duration
timeout $MONITOR_DURATION vercel logs --follow | while IFS= read -r line; do
    format_log "$line"
done

# Summary
echo ""
echo "================================"
echo "📊 Monitoring Summary"
echo "================================"

if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c "\[ERROR\]" "$LOG_FILE" || echo "0")
    WARN_COUNT=$(grep -c "\[WARN\]" "$LOG_FILE" || echo "0")
    TOTAL_LINES=$(wc -l < "$LOG_FILE" | tr -d ' ')
    
    echo "Total log entries: $TOTAL_LINES"
    echo -e "Errors: ${RED}$ERROR_COUNT${NC}"
    echo -e "Warnings: ${YELLOW}$WARN_COUNT${NC}"
    echo ""
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "Recent errors:"
        grep "\[ERROR\]" "$LOG_FILE" | tail -5
    fi
fi

echo ""
echo "Log saved to: $LOG_FILE"