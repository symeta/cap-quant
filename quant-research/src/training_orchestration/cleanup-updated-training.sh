#!/bin/bash

# 清理更新的模型训练资源脚本

set -e

echo "=== 清理更新的模型训练资源 ==="

# 删除RayCluster
echo "1. 删除RayCluster..."
if kubectl get raycluster kuberay-trn1-updated &> /dev/null; then
    kubectl delete raycluster kuberay-trn1-updated
    echo "RayCluster 'kuberay-trn1-updated' 已删除"
else
    echo "RayCluster 'kuberay-trn1-updated' 不存在"
fi

# 删除ConfigMap
echo "2. 删除ConfigMap..."
if kubectl get configmap updated-model-code &> /dev/null; then
    kubectl delete configmap updated-model-code
    echo "ConfigMap 'updated-model-code' 已删除"
else
    echo "ConfigMap 'updated-model-code' 不存在"
fi

# 删除Queue
echo "3. 删除Volcano Queue..."
if kubectl get queue updated-model-training-queue &> /dev/null; then
    kubectl delete queue updated-model-training-queue
    echo "Queue 'updated-model-training-queue' 已删除"
else
    echo "Queue 'updated-model-training-queue' 不存在"
fi

# 可选：删除PVC（注意这会删除数据）
read -p "是否删除JuiceFS PVC? 这将删除所有训练数据 (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "4. 删除JuiceFS PVC..."
    if kubectl get pvc jfs-dataset &> /dev/null; then
        kubectl delete pvc jfs-dataset
        echo "PVC 'jfs-dataset' 已删除"
    else
        echo "PVC 'jfs-dataset' 不存在"
    fi
else
    echo "4. 保留JuiceFS PVC"
fi

echo ""
echo "=== 清理完成 ==="
echo ""
echo "剩余资源:"
echo "Pods:"
kubectl get pods -l ray.io/cluster=kuberay-trn1-updated 2>/dev/null || echo "无相关Pods"
echo ""
echo "PVCs:"
kubectl get pvc jfs-dataset 2>/dev/null || echo "无JuiceFS PVC"
