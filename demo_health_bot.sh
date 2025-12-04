#!/bin/bash
# Demo script for DevOps Health Bot

echo "🤖 DevOps Health Bot - Demo"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check current containers
CONTAINER_COUNT=$(docker ps -q | wc -l)
echo "📊 Current containers: $CONTAINER_COUNT"
echo ""

# If no containers, offer to start some test containers
if [ $CONTAINER_COUNT -eq 0 ]; then
    echo "No containers running. Would you like to start some test containers? (y/n)"
    read -r response
    
    if [ "$response" = "y" ]; then
        echo ""
        echo "🚀 Starting test containers..."
        
        # Start test containers
        docker run -d --name test-web-healthy nginx:alpine > /dev/null 2>&1
        docker run -d --name test-api-prod python:3.9-alpine python -m http.server 8000 > /dev/null 2>&1
        docker run -d --name test-worker-staging alpine sleep 3600 > /dev/null 2>&1
        
        echo "✅ Started 3 test containers"
        echo "   - test-web-healthy (nginx)"
        echo "   - test-api-prod (python)"
        echo "   - test-worker-staging (alpine)"
        echo ""
        
        # Wait a moment for containers to start
        sleep 2
    fi
fi

# Show current containers
echo "📋 Current Docker containers:"
echo "----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""

# Run the health bot tests
echo "🧪 Running DevOps Health Bot tests..."
echo "=========================================="
echo ""

python3 test_health_bot.py

echo ""
echo "=========================================="
echo "✅ Demo complete!"
echo ""
echo "Next steps:"
echo "  1. Try in the TUI: python demo.py"
echo "     Then use: /ai, /ai prod, /ai web"
echo ""
echo "  2. Set up IRC bridge: python kiro_irc_bridge.py"
echo "     Then use: !ai in your IRC channel"
echo ""
echo "  3. Read the docs: DEVOPS_HEALTH_BOT.md"
echo ""

# Offer to clean up test containers
if docker ps -a --format '{{.Names}}' | grep -q "^test-"; then
    echo "Clean up test containers? (y/n)"
    read -r cleanup
    
    if [ "$cleanup" = "y" ]; then
        echo ""
        echo "🧹 Cleaning up test containers..."
        docker stop test-web-healthy test-api-prod test-worker-staging > /dev/null 2>&1
        docker rm test-web-healthy test-api-prod test-worker-staging > /dev/null 2>&1
        echo "✅ Test containers removed"
    fi
fi

echo ""
echo "Goodbye! 👋"
