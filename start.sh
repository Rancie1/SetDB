#!/bin/bash

# Start script for Deckd - starts both backend and frontend servers

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Starting Deckd servers...${NC}\n"

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${YELLOW}❌ Error: backend directory not found${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${YELLOW}❌ Error: frontend directory not found${NC}"
    exit 1
fi

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}❌ Error: backend/venv not found. Please set up the backend first.${NC}"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start backend server
echo -e "${BLUE}📦 Starting backend server...${NC}"
cd backend
source venv/bin/activate

# Start backend - output will be visible in terminal
# Using a subshell to keep it in background but output visible
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${YELLOW}❌ Backend failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend running on http://localhost:8000 (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}   Backend logs will appear in this terminal${NC}\n"

# Start frontend server
echo -e "${BLUE}🎨 Starting frontend server...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Start frontend (this will run in foreground)
echo -e "${GREEN}✓ Frontend starting on http://localhost:5173${NC}\n"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Both servers are running!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

npm run dev
