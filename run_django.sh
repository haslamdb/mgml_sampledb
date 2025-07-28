#!/bin/bash

# MGML Sample Database - Proper Virtual Environment Usage
# This script properly activates the virtual environment and runs Django commands

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧬 MGML Sample Database - Virtual Environment Manager${NC}"
echo -e "${BLUE}======================================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please create a virtual environment first:${NC}"
    echo "python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo -e "${RED}❌ Django not found in virtual environment!${NC}"
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install -r requirements.txt
fi

# Show current environment info
echo -e "${GREEN}✅ Virtual environment activated!${NC}"
echo -e "${BLUE}Python path: $(which python)${NC}"
echo -e "${BLUE}Python version: $(python --version)${NC}"
echo -e "${BLUE}Django version: $(python -c "import django; print(django.get_version())")${NC}"

# Function to run Django commands
run_django_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "\n${YELLOW}$description...${NC}"
    python manage.py $cmd
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ $description completed successfully!${NC}"
    else
        echo -e "${RED}❌ $description failed with exit code $exit_code${NC}"
        return $exit_code
    fi
}

# Parse command line arguments
case "${1:-help}" in
    "server"|"runserver")
        echo -e "\n${BLUE}🚀 Starting Django development server...${NC}"
        run_django_command "collectstatic --noinput" "Collecting static files"
        run_django_command "migrate" "Running database migrations"
        echo -e "\n${GREEN}🌐 Django server will be available at: http://localhost:8000${NC}"
        echo -e "${GREEN}📊 Admin interface: http://localhost:8000/admin/${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}\n"
        python manage.py runserver 0.0.0.0:8000
        ;;
    "shell")
        echo -e "\n${BLUE}🐍 Starting Django shell...${NC}"
        python manage.py shell
        ;;
    "migrate")
        run_django_command "migrate" "Running database migrations"
        ;;
    "makemigrations")
        run_django_command "makemigrations" "Creating database migrations"
        ;;
    "collectstatic")
        run_django_command "collectstatic --noinput" "Collecting static files"
        ;;
    "createsuperuser")
        run_django_command "createsuperuser" "Creating superuser"
        ;;
    "check")
        run_django_command "check" "Running Django system check"
        ;;
    "admin_dashboard")
        run_django_command "admin_dashboard" "Generating admin dashboard report"
        ;;
    "security_audit")
        run_django_command "security_audit" "Running security audit"
        ;;
    "test")
        run_django_command "test" "Running tests"
        ;;
    "help"|*)
        echo -e "\n${GREEN}📖 Available commands:${NC}"
        echo -e "  ${BLUE}server${NC}         - Start Django development server"
        echo -e "  ${BLUE}shell${NC}          - Start Django shell"
        echo -e "  ${BLUE}migrate${NC}        - Run database migrations"
        echo -e "  ${BLUE}makemigrations${NC} - Create database migrations"
        echo -e "  ${BLUE}collectstatic${NC}  - Collect static files"
        echo -e "  ${BLUE}createsuperuser${NC} - Create admin superuser"
        echo -e "  ${BLUE}check${NC}          - Run Django system check"
        echo -e "  ${BLUE}admin_dashboard${NC} - Generate admin dashboard report"
        echo -e "  ${BLUE}security_audit${NC}  - Run security audit"
        echo -e "  ${BLUE}test${NC}           - Run tests"
        echo -e "  ${BLUE}help${NC}           - Show this help message"
        echo -e "\n${YELLOW}Examples:${NC}"
        echo -e "  ./run_django.sh server"
        echo -e "  ./run_django.sh migrate"
        echo -e "  ./run_django.sh collectstatic"
        ;;
esac
