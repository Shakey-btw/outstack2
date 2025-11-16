#!/bin/bash
# Analyze backend logs for performance metrics

echo "📊 Analyzing Backend Performance Logs"
echo "======================================"
echo ""

# Check if there are any log files or we need to check the console output
echo "Looking for performance metrics in recent backend output..."
echo ""
echo "Key metrics to look for:"
echo "- Activities duration (parallel fetch time)"
echo "- Total campaign duration"
echo "- Average time per campaign"
echo ""

# If backend is running, we can't easily capture logs from here
# But we can provide instructions
echo "To see detailed performance logs:"
echo "1. Check your backend server console output"
echo "2. Look for lines containing:"
echo "   - 'activities: X.Xs' (parallel activities fetch time)"
echo "   - 'total: X.Xs' (total campaign processing time)"
echo "   - 'Performance:' (summary metrics)"
echo ""

