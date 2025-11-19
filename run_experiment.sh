#!/bin/bash

# run_experiment.sh - Simple Docker wrapper with dynamic environment variables
# Usage: ./run_experiment.sh <python_script> <python arg_1> <python arg_2> ...


set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONFIG_FILE="$PROJECT_DIR/EditBench.config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="editbench:latest"
PYTHON_VERSION="3.12"

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        echo -e "${RED} EditBench.config file not found. Please create an EditBench.config and run again.${NC}"
        exit 1
    fi
}

# Build dynamic environment variable flags from config file
build_env_flags() {
    local env_flags=""
    local hf_token_found=false
    
    # Always add WORKDIR (not from config)
    env_flags+=" --env WORKDIR=/project"
    
    if [ -f "$CONFIG_FILE" ]; then
        # Read config file and extract all variable assignments
        while IFS= read -r line; do
            # Skip empty lines and comments
            if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
                continue
            fi
            
            # Extract variable name and value (handle = with optional spaces)
            if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
                var_name="${BASH_REMATCH[1]}"
                var_value="${BASH_REMATCH[2]}"
                
                # Remove quotes if present
                var_value=$(echo "$var_value" | sed 's/^"//;s/"$//')
                
                # Check if this is HF_TOKEN
                if [[ "$var_name" == "HF_TOKEN" ]]; then
                    hf_token_found=true
                fi
                
                # Add to environment flags
                env_flags+=" --env ${var_name}=${var_value}"
            fi
        done < "$CONFIG_FILE"
    fi
    
    # # If HF_TOKEN wasn't found in config, try to use the default from environment
    # if [ "$hf_token_found" = false ] && [ -n "$HF_TOKEN" ]; then
    #     env_flags+=" --env HF_TOKEN=${HF_TOKEN}"
    # fi
    
    echo "$env_flags"
}

validate_config() {
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}Project directory does not exist: $PROJECT_DIR${NC}"
        exit 1
    fi
}

image_exists() {
    docker images -q "$IMAGE_NAME" | grep -q .
}

build_if_needed() {
    if ! image_exists; then
        echo -e "${YELLOW}Docker image not found. Building...${NC}"
        docker buildx build --load -t "$IMAGE_NAME" \
            --build-arg PYTHON_VERSION="$PYTHON_VERSION" \
            "$PROJECT_DIR"
        echo -e "${GREEN}✓ Build complete${NC}"
    fi
}

run_script() {
    local python_script="$1"
    shift  # Remove first argument, leaving optional args
    
    echo -e "${GREEN}Running: $python_script${NC}"
    if [ $# -gt 0 ]; then
        echo -e "${BLUE}Arguments: $@${NC}"
    fi
    echo -e "${BLUE}Project: $PROJECT_DIR${NC}"
    
    # Get dynamic environment flags
    ENV_FLAGS=$(build_env_flags)
    
    # Debug: show what environment variables will be passed
    echo -e "${BLUE}Environment variables: $(echo $ENV_FLAGS | sed 's/--env /\n  • /g' | tail -n +2)${NC}"
    
    docker run -t --rm \
        --mount type=bind,src="$PROJECT_DIR",dst=/project \
        $ENV_FLAGS \
        "$IMAGE_NAME" python3 -u "/project/$python_script" "$@"
}

# Main usage - requires at least 1 argument (python script)
if [ $# -ge 1 ] && [[ ! "$1" =~ ^(shell|sh|build|env|help|--help|-h)$ ]]; then
    load_config
    validate_config
    build_if_needed
    run_script "$@"
    exit 0
fi

# Advanced usage with specific commands
case "${1:-}" in
    "shell"|"sh")
        load_config
        validate_config
        build_if_needed
        echo -e "${GREEN}Starting interactive shell...${NC}"
        
        # Get dynamic environment flags
        ENV_FLAGS=$(build_env_flags)
        
        docker run -it --rm \
            --mount type=bind,src="$PROJECT_DIR",dst=/project \
            $ENV_FLAGS \
            "$IMAGE_NAME"
        ;;
    "build")
        load_config
        validate_config
        echo -e "${GREEN}Building Docker image...${NC}"
        docker buildx build --load -t "$IMAGE_NAME" \
            --build-arg PYTHON_VERSION="$PYTHON_VERSION" \
            "$PROJECT_DIR"
        echo -e "${GREEN}✓ Build complete${NC}"
        ;;
    "env")
        load_config
        echo -e "${GREEN}Environment variables from config:${NC}"
        ENV_FLAGS=$(build_env_flags)
        echo "$ENV_FLAGS" | sed 's/--env /\n  • /g' | tail -n +2
        ;;
    "help"|"--help"|"-h")
        echo "HumanEditBench Docker Wrapper"
        echo ""
        echo "Main usage:"
        echo "  ./run_experiment.sh <python_script> [args...]  # Run script with optional arguments"
        echo ""
        echo "Advanced usage:"
        echo "  ./run_experiment.sh shell        # Interactive shell"
        echo "  ./run_experiment.sh build        # Force rebuild"
        echo "  ./run_experiment.sh env          # Show environment variables from config"
        echo ""
        echo "Examples:"
        echo "  ./run_experiment.sh examples/run_gpt_o3_mini_tests.py"
        echo "  ./run_experiment.sh examples/run_gpt_o3_mini_experiment.py --should_generate"
        echo "  ./run_experiment.sh examples/openai_experiment.py configs/gpt-o3-mini.json"
        echo "  ./run_experiment.sh your_custom_script.py --verbose --output results.txt --whatever_you_want"
        echo ""
        echo "Dynamic environment variables:"
        echo "  All variables in EditBench.config are automatically passed to the container"
        ;;
    *)
        echo -e "${RED}Error: Invalid usage${NC}"
        echo ""
        echo "Usage: ./run_experiment.sh <python_script> [args...]"
        echo "   or: ./run_experiment.sh [shell|build|env|help]"
        echo ""
        echo "Run './run_experiment.sh help' for more information"
        exit 1
        ;;
esac