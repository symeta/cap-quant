#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Neuron Model Training Docker Setup ===${NC}"

# 检查必要文件
echo -e "${YELLOW}Checking required files...${NC}"
required_files=("model_updated.py" "train_updated.py" "Dockerfile.neuron")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}Error: $file not found!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $file found${NC}"
done

# 创建必要的目录
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p data checkpoints logs tensorboard_logs
echo -e "${GREEN}✓ Directories created${NC}"

# 构建 Docker 镜像
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f Dockerfile.neuron -t neuron-model-training:latest .

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

# 显示使用说明
echo -e "${GREEN}=== Build Complete ===${NC}"
echo ""
echo -e "${YELLOW}Usage Options:${NC}"
echo ""
echo -e "${GREEN}1. Run training directly:${NC}"
echo "   docker run --rm -v \$(pwd)/checkpoints:/app/checkpoints neuron-model-training:latest"
echo ""
echo -e "${GREEN}2. Run with Docker Compose (recommended):${NC}"
echo "   docker-compose up neuron-training"
echo ""
echo -e "${GREEN}3. Run with TensorBoard:${NC}"
echo "   docker-compose up"
echo ""
echo -e "${GREEN}4. Interactive mode:${NC}"
echo "   docker run -it --rm -v \$(pwd):/app/workspace neuron-model-training:latest /bin/bash"
echo ""
echo -e "${GREEN}5. Check environment only:${NC}"
echo "   docker run --rm neuron-model-training:latest /app/check_env.sh"
echo ""

# 询问是否立即运行
read -p "Do you want to run the training now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Starting training...${NC}"
    docker run --rm \
        -v $(pwd)/checkpoints:/app/checkpoints \
        -v $(pwd)/logs:/app/logs \
        neuron-model-training:latest
    
    echo -e "${GREEN}Training completed! Check the checkpoints/ directory for results.${NC}"
fi
