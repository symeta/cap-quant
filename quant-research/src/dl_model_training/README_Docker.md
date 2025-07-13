# Neuron Model Training Docker Setup

这个项目包含了将 MNIST 模型训练代码（基于 Neuron SDK 2.24.0）打包成 Docker 镜像的完整配置。

## 文件结构

```
.
├── Dockerfile                 # 通用 PyTorch 镜像（用于开发测试）
├── Dockerfile.neuron         # AWS Neuron 专用镜像（生产环境）
├── docker-compose.yml        # Docker Compose 配置
├── build_and_run.sh         # 自动构建和运行脚本
├── model_updated.py         # 更新的模型文件
├── train_updated.py         # 更新的训练脚本
└── README_Docker.md         # 本文档
```

## 快速开始

### 方法 1: 使用自动化脚本（推荐）

```bash
./build_and_run.sh
```

这个脚本会：
- 检查必要文件
- 创建所需目录
- 构建 Docker 镜像
- 提供多种运行选项

### 方法 2: 手动构建和运行

#### 构建镜像

```bash
# 构建 Neuron 专用镜像
docker build -f Dockerfile.neuron -t neuron-model-training:latest .

# 或构建通用镜像（用于开发）
docker build -f Dockerfile -t pytorch-model-training:latest .
```

#### 运行训练

```bash
# 基本运行
docker run --rm -v $(pwd)/checkpoints:/app/checkpoints neuron-model-training:latest

# 交互式运行
docker run -it --rm -v $(pwd):/app/workspace neuron-model-training:latest /bin/bash

# 检查环境
docker run --rm neuron-model-training:latest /app/check_env.sh
```

### 方法 3: 使用 Docker Compose

```bash
# 运行训练
docker-compose up neuron-training

# 运行训练 + TensorBoard
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f neuron-training
```

## 环境要求

### 在 AWS Trainium/Inferentia 实例上运行

如果你在 AWS Trainium (trn1) 或 Inferentia (inf1/inf2) 实例上运行：

```bash
# 需要设备访问权限
docker run --privileged --device=/dev/neuron0:/dev/neuron0 \
    -v $(pwd)/checkpoints:/app/checkpoints \
    neuron-model-training:latest
```

### 在普通 GPU/CPU 实例上运行

```bash
# 使用通用镜像
docker run --rm -v $(pwd)/checkpoints:/app/checkpoints \
    pytorch-model-training:latest
```

## 配置选项

### 环境变量

- `NEURON_RT_NUM_CORES`: Neuron 核心数量（默认: 1）
- `NEURON_CC_FLAGS`: Neuron 编译器标志
- `PYTHONUNBUFFERED`: Python 输出缓冲（默认: 1）

### 卷挂载

- `/app/checkpoints`: 模型检查点保存位置
- `/app/logs`: 训练日志
- `/app/tensorboard_logs`: TensorBoard 日志
- `/app/MNIST_DATA_train`: MNIST 数据集

## 服务端口

- `6006`: TensorBoard
- `8888`: Jupyter Notebook（可选）

## 使用示例

### 1. 基本训练

```bash
docker run --rm \
    -v $(pwd)/checkpoints:/app/checkpoints \
    -v $(pwd)/logs:/app/logs \
    neuron-model-training:latest
```

### 2. 带 TensorBoard 监控

```bash
docker-compose up
# 然后访问 http://localhost:6006 查看 TensorBoard
```

### 3. 开发模式

```bash
docker run -it --rm \
    -v $(pwd):/app/workspace \
    -p 8888:8888 \
    neuron-model-training:latest /bin/bash
```

### 4. 自定义配置

```bash
docker run --rm \
    -e NEURON_RT_NUM_CORES=2 \
    -e NEURON_CC_FLAGS="--model-type=transformer --optimization-level=2" \
    -v $(pwd)/checkpoints:/app/checkpoints \
    neuron-model-training:latest
```

## 故障排除

### 1. 检查环境

```bash
docker run --rm neuron-model-training:latest /app/check_env.sh
```

### 2. 查看日志

```bash
docker-compose logs neuron-training
```

### 3. 进入容器调试

```bash
docker run -it --rm neuron-model-training:latest /bin/bash
```

### 4. 常见问题

- **Neuron 设备未找到**: 确保在 Trainium/Inferentia 实例上运行，并使用 `--privileged` 标志
- **权限问题**: 检查挂载目录的权限
- **内存不足**: 减少 batch size 或使用更大的实例

## 输出文件

训练完成后，你会在以下位置找到输出：

- `checkpoints/checkpoint.pt`: 训练好的模型
- `logs/`: 训练日志
- `tensorboard_logs/`: TensorBoard 日志文件

## 扩展功能

### 添加新的训练脚本

1. 将新脚本复制到容器中（修改 Dockerfile）
2. 更新启动脚本
3. 重新构建镜像

### 集成其他监控工具

可以轻松集成 Weights & Biases、MLflow 等工具：

```dockerfile
RUN pip install wandb mlflow
```

## 生产部署

对于生产环境，建议：

1. 使用多阶段构建优化镜像大小
2. 设置健康检查
3. 使用 Kubernetes 进行编排
4. 配置日志聚合
5. 设置监控和告警
