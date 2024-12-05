#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_message "$RED" "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Function to check if Nvidia GPU is available
check_nvidia_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            return 0 # GPU available
        fi
    fi
    return 1 # GPU not available
}

# Function to check if Nvidia Container Toolkit is installed
check_nvidia_toolkit() {
    if ! docker info | grep -i "nvidia" &> /dev/null; then
        print_message "$YELLOW" "Warning: Nvidia Container Toolkit not detected. GPU support may not work."
        print_message "$YELLOW" "To install, visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi
    return 0
}

# Function to stop and remove existing container
cleanup_existing() {
    if docker ps -a | grep -q "ollama"; then
        print_message "$YELLOW" "Stopping and removing existing Ollama container..."
        docker stop ollama &> /dev/null
        docker rm ollama &> null
    fi
}

# Function to start Ollama
start_ollama() {
    local use_gpu=$1
    
    if [ "$use_gpu" = true ] && check_nvidia_gpu && check_nvidia_toolkit; then
        print_message "$GREEN" "Setting up Ollama with GPU support..."
        docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    else
        if [ "$use_gpu" = true ]; then
            print_message "$YELLOW" "GPU setup requested but not available. Falling back to CPU..."
        else
            print_message "$GREEN" "Setting up Ollama with CPU..."
        fi
        docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    fi
}

# Function to wait for Ollama to be ready
wait_for_ollama() {
    print_message "$GREEN" "Waiting for Ollama to start..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            print_message "$GREEN" "Ollama is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_message "$RED" "Timeout waiting for Ollama to start"
    return 1
}

# Function to exit Ollama
exit_ollama() {
    print_message "$YELLOW" "Stopping Ollama container..."
    docker stop ollama &> /dev/null
}

# Function to chat with Ollama
chat_ollama() {
    local message=$1
    local model="llama3" 
    response=$(curl -s -X POST http://localhost:11434/api/chat -d "{\"message\": \"$message\", \"model\": \"$model\"}" -H "Content-Type: application/json")
    if echo "$response" | grep -q "error"; then
        print_message "$RED" "Failed to send message to Ollama: $response"
    else
        print_message "$GREEN" "Message sent to Ollama: $response"
    fi
}

# Function to pull Ollama Docker images
pull_ollama_images() {
    print_message "$GREEN" "Pulling Ollama Docker images..."
    docker pull ollama/ollama
}

# Function to delete Ollama Docker images
delete_ollama_images() {
    print_message "$YELLOW" "Stopping and removing existing Ollama container..."
    docker stop ollama &> /dev/null
    docker rm ollama &> /dev/null
    print_message "$YELLOW" "Deleting Ollama Docker images..."
    docker rmi ollama/ollama
}

# Function to display help message
display_help() {
    echo "Usage: $0 {start|exit|chat <message>|pull|delete|--help}"
    echo
    echo "Commands:"
    echo "  start          Start the Ollama container"
    echo "  exit           Stop the Ollama container"
    echo "  chat <message> Send a chat message to Ollama"
    echo "  pull           Pull the Ollama Docker images"
    echo "  delete         Delete the Ollama Docker images"
    echo "  --help         Display this help message"
}

# Main script execution
main() {
    check_docker
    
    case "$1" in
        start)
            cleanup_existing
            local use_gpu=false
            if check_nvidia_gpu; then
                use_gpu=true
            fi
            start_ollama $use_gpu
            wait_for_ollama
            ;;
        exit)
            exit_ollama
            ;;
        chat)
            if [ -z "$2" ]; then
                print_message "$RED" "Error: No message provided for chat"
                exit 1
            fi
            chat_ollama "$2"
            ;;
        pull)
            pull_ollama_images
            ;;
        delete)
            delete_ollama_images
            ;;
        --help)
            display_help
            ;;
        *)
            print_message "$YELLOW" "Invalid command. Use --help to see the available commands."
            exit 1
            ;;
    esac
}

# Run the script
main "$@"