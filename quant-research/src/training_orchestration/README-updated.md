# 更新的模型训练配置

本配置将原有的训练脚本进行了以下更新：

## 主要变更

### 1. 模型更新
- **原模型**: 使用原有的Llama2模型
- **新模型**: 使用 `../dl_model_training/model_updated.py` 和 `train_updated.py` 中定义的MLP模型
- **特性**: 
  - 针对Neuron SDK 2.24.0优化
  - 支持混合精度训练
  - 添加了dropout层提高泛化能力

### 2. 存储更新
- **原存储**: FSx for Lustre
- **新存储**: JuiceFS (通过Fluid创建的dataset)
- **优势**: 
  - 更灵活的存储配置
  - 支持多种后端存储
  - 更好的成本控制

## 文件说明

- `llama2-pretrain-trn1-raycluster-updated.yaml`: 更新的RayCluster配置文件
- `deploy-updated-training.sh`: 部署脚本
- `cleanup-updated-training.sh`: 清理脚本
- `README-updated.md`: 本说明文件

## 部署前准备

### 1. 确保JuiceFS环境已部署

```bash
# 部署JuiceFS secret
kubectl apply -f ../../yaml/juicefs/jfs-secret.yaml

# 部署JuiceFS dataset
kubectl apply -f ../../yaml/juicefs/jfs-dataset.yaml

# 部署JuiceFS runtime
kubectl apply -f ../../yaml/juicefs/jfs-runtime.yaml

# 检查状态
kubectl get dataset jfs-dataset -n fluid-system
kubectl get juicefsruntime jfs-dataset -n fluid-system
```

### 2. 确保EKS集群配置正确

- Trn1实例节点组已配置
- Neuron device plugin已安装
- EFA支持已启用
- Volcano调度器已部署

## 部署步骤

### 方法1: 使用部署脚本（推荐）

```bash
# 运行部署脚本
./deploy-updated-training.sh
```

### 方法2: 手动部署

```bash
# 1. 检查JuiceFS dataset状态
kubectl get dataset jfs-dataset -n fluid-system

# 2. 等待dataset就绪
kubectl wait --for=condition=Ready dataset/jfs-dataset -n fluid-system --timeout=300s

# 3. 部署训练配置
kubectl apply -f llama2-pretrain-trn1-raycluster-updated.yaml

# 4. 等待RayCluster就绪
kubectl wait --for=condition=Ready raycluster/kuberay-trn1-updated --timeout=600s
```

## 使用方法

### 1. 访问Ray Dashboard

```bash
kubectl port-forward service/kuberay-trn1-updated-head-svc 8265:8265
```

然后在浏览器中访问: http://localhost:8265

### 2. 启动训练任务

```bash
# 获取head pod名称
HEAD_POD=$(kubectl get pods -l ray.io/group=headgroup,ray.io/cluster=kuberay-trn1-updated -o jsonpath='{.items[0].metadata.name}')

# 执行训练
kubectl exec -it $HEAD_POD -- python /app/model/train_updated.py
```

### 3. 查看训练日志

```bash
# 查看所有相关pod的日志
kubectl logs -l ray.io/cluster=kuberay-trn1-updated -f

# 或者查看特定pod的日志
kubectl logs $HEAD_POD -f
```

### 4. 监控训练进度

```bash
# 查看pod状态
kubectl get pods -l ray.io/cluster=kuberay-trn1-updated

# 查看资源使用情况
kubectl top pods -l ray.io/cluster=kuberay-trn1-updated
```

## 数据和模型存储

### 训练数据
- 存储位置: `/shared/MNIST_DATA_train` (JuiceFS挂载点)
- 自动下载: 首次运行时自动下载MNIST数据集

### 模型检查点
- 存储位置: `/shared/checkpoints/checkpoint.pt`
- 持久化: 保存在JuiceFS中，训练完成后可持久访问

### 模型代码
- 挂载位置: `/app/model/`
- 来源: ConfigMap (从本地文件创建)

## 故障排除

### 1. JuiceFS相关问题

```bash
# 检查dataset状态
kubectl describe dataset jfs-dataset -n fluid-system

# 检查runtime状态
kubectl describe juicefsruntime jfs-dataset -n fluid-system

# 检查PVC状态
kubectl describe pvc jfs-dataset
```

### 2. 训练任务问题

```bash
# 查看详细日志
kubectl logs $HEAD_POD --previous

# 检查资源分配
kubectl describe pod $HEAD_POD

# 检查Neuron设备
kubectl exec -it $HEAD_POD -- neuron-ls
```

### 3. 网络问题

```bash
# 检查EFA设备
kubectl exec -it $WORKER_POD -- fi_info -p efa

# 检查Ray集群连接
kubectl exec -it $HEAD_POD -- ray status
```

## 清理资源

### 使用清理脚本

```bash
./cleanup-updated-training.sh
```

### 手动清理

```bash
# 删除RayCluster
kubectl delete raycluster kuberay-trn1-updated

# 删除ConfigMap
kubectl delete configmap updated-model-code

# 删除Queue
kubectl delete queue updated-model-training-queue

# 可选：删除PVC（会删除数据）
kubectl delete pvc jfs-dataset
```

## 性能优化建议

1. **批处理大小**: 根据Trn1实例内存调整BATCH_SIZE
2. **并行度**: 调整worker replicas数量
3. **存储优化**: 使用JuiceFS缓存提高I/O性能
4. **网络优化**: 确保EFA正确配置以获得最佳网络性能

## 监控和日志

- Ray Dashboard: 集群状态和任务监控
- Kubernetes Dashboard: 资源使用监控
- CloudWatch: AWS资源监控
- JuiceFS监控: 存储I/O性能监控
