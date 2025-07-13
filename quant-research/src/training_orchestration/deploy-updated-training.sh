#!/bin/bash

# 部署更新的模型训练配置脚本
# 使用JuiceFS存储和更新的模型文件

set -e

echo "=== 部署更新的模型训练配置 ==="

# 检查必要的前置条件
echo "1. 检查JuiceFS dataset是否存在..."
if ! kubectl get dataset jfs-dataset -n fluid-system &> /dev/null; then
    echo "错误: JuiceFS dataset 'jfs-dataset' 不存在于 fluid-system namespace"
    echo "请先部署JuiceFS dataset和runtime:"
    echo "  kubectl apply -f ../../yaml/juicefs/jfs-secret.yaml"
    echo "  kubectl apply -f ../../yaml/juicefs/jfs-dataset.yaml"
    echo "  kubectl apply -f ../../yaml/juicefs/jfs-runtime.yaml"
    exit 1
fi

echo "2. 检查JuiceFS runtime是否就绪..."
if ! kubectl get juicefsruntime jfs-dataset -n fluid-system &> /dev/null; then
    echo "错误: JuiceFS runtime 'jfs-dataset' 不存在于 fluid-system namespace"
    echo "请先部署JuiceFS runtime:"
    echo "  kubectl apply -f ../../yaml/juicefs/jfs-runtime.yaml"
    exit 1
fi

# 等待JuiceFS dataset就绪
echo "3. 等待JuiceFS dataset就绪..."
kubectl wait --for=condition=Ready dataset/jfs-dataset -n fluid-system --timeout=300s

# 检查PVC是否创建
echo "4. 检查JuiceFS PVC是否创建..."
if ! kubectl get pvc jfs-dataset -n default &> /dev/null; then
    echo "警告: PVC 'jfs-dataset' 不存在于 default namespace"
    echo "尝试创建PVC..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jfs-dataset
  namespace: default
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: fluid
  selector:
    matchLabels:
      fluid.io/dataset: fluid-system.jfs-dataset
EOF
fi

# 部署更新的训练配置
echo "5. 部署更新的RayCluster配置..."
kubectl apply -f llama2-pretrain-trn1-raycluster-updated.yaml

echo "6. 等待RayCluster就绪..."
kubectl wait --for=condition=Ready raycluster/kuberay-trn1-updated --timeout=600s

echo "7. 检查部署状态..."
echo "RayCluster状态:"
kubectl get raycluster kuberay-trn1-updated -o wide

echo ""
echo "Pod状态:"
kubectl get pods -l ray.io/cluster=kuberay-trn1-updated

echo ""
echo "=== 部署完成 ==="
echo ""
echo "访问Ray Dashboard:"
echo "kubectl port-forward service/kuberay-trn1-updated-head-svc 8265:8265"
echo "然后在浏览器中访问: http://localhost:8265"
echo ""
echo "查看训练日志:"
echo "kubectl logs -l ray.io/cluster=kuberay-trn1-updated -f"
echo ""
echo "启动训练任务:"
echo "kubectl exec -it \$(kubectl get pods -l ray.io/group=headgroup,ray.io/cluster=kuberay-trn1-updated -o jsonpath='{.items[0].metadata.name}') -- python /app/model/train_updated.py"
