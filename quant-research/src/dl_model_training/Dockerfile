# 使用官方的 PyTorch 基础镜像，支持 CUDA
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Neuron SDK 2.24.0 相关依赖
RUN pip install --upgrade pip

# 安装 PyTorch XLA 和 Neuron SDK 2.24.0
RUN pip install torch-xla[tpu]==2.1.0 -f https://storage.googleapis.com/libtpu-releases/index.html
RUN pip install neuronx-cc==2.24.0
RUN pip install torch-neuronx==2.24.0

# 安装其他必要的 Python 包
RUN pip install \
    torchvision \
    numpy \
    matplotlib \
    tqdm \
    tensorboard

# 复制模型和训练脚本
COPY model_updated.py /app/
COPY train_updated.py /app/

# 复制原始文件作为备份（如果需要）
COPY model.py /app/model_original.py
COPY train.py /app/train_original.py

# 创建数据和检查点目录
RUN mkdir -p /app/MNIST_DATA_train
RUN mkdir -p /app/checkpoints
RUN mkdir -p /app/logs

# 设置权限
RUN chmod +x /app/*.py

# 暴露端口（如果需要 TensorBoard 或其他服务）
EXPOSE 6006

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "Starting model training with Neuron SDK 2.24.0..."\n\
echo "Python version: $(python --version)"\n\
echo "PyTorch version: $(python -c \"import torch; print(torch.__version__)\")"\n\
echo "Torch XLA version: $(python -c \"import torch_xla; print(torch_xla.__version__)\" 2>/dev/null || echo \"Not available\")\"\n\
echo "Current directory: $(pwd)"\n\
echo "Files in directory: $(ls -la)"\n\
echo ""\n\
echo "Running training..."\n\
python train_updated.py\n\
echo "Training completed!"\n\
echo "Checkpoint saved in: $(ls -la checkpoints/)"\n\
' > /app/run_training.sh

RUN chmod +x /app/run_training.sh

# 默认命令
CMD ["/app/run_training.sh"]
