#!/bin/bash
#
# Quick deployment verification script for Aptly
#
# Usage:
#   ./scripts/verify_deployment.sh https://your-app.railway.app
#
# This script performs a quick health check to verify the deployment is working.
# For full verification, use smoke_test.py instead.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: No URL provided${NC}"
    echo "Usage: $0 <base-url>"
    echo "Example: $0 https://your-app.railway.app"
    exit 1
fi

BASE_URL="${1%/}"  # Remove trailing slash if present

echo ""
echo "========================================"
echo "Aptly Deployment Verification"
echo "========================================"
echo "Target: $BASE_URL"
echo ""

# Health check
echo -n "Checking health endpoint... "
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}OK${NC}"

    # Parse and display health details
    STATUS=$(echo "$BODY" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    VERSION=$(echo "$BODY" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    DB_STATUS=$(echo "$BODY" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
    REDIS_STATUS=$(echo "$BODY" | grep -o '"redis":"[^"]*"' | cut -d'"' -f4)

    echo ""
    echo "  Status:   $STATUS"
    echo "  Version:  $VERSION"
    echo "  Database: $DB_STATUS"
    echo "  Redis:    $REDIS_STATUS"

    # Check individual services
    if [ "$DB_STATUS" != "ok" ]; then
        echo -e "\n${YELLOW}Warning: Database check failed${NC}"
    fi

    if [ "$REDIS_STATUS" != "ok" ]; then
        echo -e "\n${YELLOW}Warning: Redis check failed${NC}"
    fi

    if [ "$STATUS" = "healthy" ]; then
        echo ""
        echo -e "${GREEN}========================================"
        echo -e "Deployment verified successfully!"
        echo -e "========================================${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Run full smoke test:"
        echo "     python scripts/smoke_test.py --url $BASE_URL --admin-secret \$APTLY_ADMIN_SECRET"
        echo ""
        echo "  2. Create your first customer:"
        echo "     curl -X POST $BASE_URL/v1/admin/customers \\"
        echo "       -H 'X-Admin-Secret: \$APTLY_ADMIN_SECRET' \\"
        echo "       -H 'Content-Type: application/json' \\"
        echo "       -d '{\"email\": \"you@example.com\", \"company_name\": \"Your Co\"}'"
        exit 0
    else
        echo ""
        echo -e "${YELLOW}========================================"
        echo -e "Deployment is degraded"
        echo -e "========================================${NC}"
        exit 1
    fi
else
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY"
    echo ""
    echo -e "${RED}========================================"
    echo -e "Deployment verification failed!"
    echo -e "========================================${NC}"
    exit 1
fi
