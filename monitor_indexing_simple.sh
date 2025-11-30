#!/bin/bash

# Simple script to monitor indexing progress

API_BASE="http://localhost:8000/api"
CHECK_INTERVAL=5
MAX_CHECKS=60  # 5 minutes max

echo "============================================================"
echo "Monitoring Content Indexing Progress"
echo "============================================================"
echo ""
echo "Checking vector count every $CHECK_INTERVAL seconds..."
echo "Press Ctrl+C to stop"
echo ""

check_count=0
last_count=0
stable_count=0

while [ $check_count -lt $MAX_CHECKS ]; do
    # Get current vector count
    response=$(curl -s "$API_BASE/rag/stats")
    current_count=$(echo "$response" | grep -o '"total_vector_count":[0-9]*' | grep -o '[0-9]*')
    
    if [ -z "$current_count" ]; then
        current_count=0
    fi
    
    timestamp=$(date '+%H:%M:%S')
    
    if [ "$current_count" -gt "$last_count" ]; then
        added=$((current_count - last_count))
        echo "[$timestamp] ✓ Vectors: $current_count (+$added)"
        last_count=$current_count
        stable_count=0
    elif [ "$current_count" -eq "$last_count" ] && [ "$current_count" -gt 0 ]; then
        stable_count=$((stable_count + 1))
        if [ $stable_count -ge 3 ]; then
            echo ""
            echo "============================================================"
            echo "✅ Indexing Complete!"
            echo "============================================================"
            echo "Total vectors indexed: $current_count"
            echo ""
            exit 0
        fi
    else
        if [ $((check_count % 6)) -eq 0 ]; then  # Print every 30 seconds
            echo "[$timestamp] ⏳ Waiting... (vectors: $current_count)"
        fi
    fi
    
    check_count=$((check_count + 1))
    sleep $CHECK_INTERVAL
done

echo ""
echo "============================================================"
echo "⚠ Monitoring timeout reached"
echo "============================================================"
echo "Current vector count: $current_count"
echo "Indexing may still be in progress. Check server logs."
echo ""


