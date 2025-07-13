import os
import time
import torch
from model import MLP

from torchvision.datasets import mnist
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor

# XLA imports - 更新到 2.24.0
import torch_xla.core.xla_model as xm
import torch_xla.distributed.parallel_loader as pl
import torch_xla.debug.metrics as met

# Global constants
EPOCHS = 4
WARMUP_STEPS = 2
BATCH_SIZE = 32

# Load MNIST train dataset
train_dataset = mnist.MNIST(root='./MNIST_DATA_train',
                            train=True, download=True, transform=ToTensor())

def main():
    # Prepare data loader
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE)
    
    # XLA: 使用 ParallelLoader 以获得更好的性能 (2.24.0 推荐)
    para_loader = pl.ParallelLoader(train_loader, [xm.xla_device()])
    train_loader = para_loader.per_device_loader(xm.xla_device())

    # Fix the random number generator seeds for reproducibility
    torch.manual_seed(0)

    # XLA: 更明确的设备指定方式 (2.24.0)
    device = xm.xla_device()
    print(f"Using device: {device}")

    # Move model to device and declare optimizer and loss function
    model = MLP().to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    loss_fn = torch.nn.NLLLoss()

    # Run the training loop
    print('----------Training ---------------')
    model.train()
    for epoch in range(EPOCHS):
        start = time.time()
        for idx, (train_x, train_label) in enumerate(train_loader):
            optimizer.zero_grad()
            train_x = train_x.view(train_x.size(0), -1)
            train_x = train_x.to(device)
            train_label = train_label.to(device)
            output = model(train_x)
            loss = loss_fn(output, train_label)
            loss.backward()
            optimizer.step()
            
            # XLA: mark_step 在 2.24.0 中保持不变，但建议添加更多调试信息
            xm.mark_step()
            
            if idx < WARMUP_STEPS: # skip warmup iterations
                start = time.time()

        # 2.24.0 新增：打印每个 epoch 的指标
        print(f"Epoch {epoch + 1}/{EPOCHS} completed")
        
        # 可选：打印 XLA 编译指标 (2.24.0 新功能)
        if epoch == 0:  # 只在第一个 epoch 后打印
            print("XLA compilation metrics:")
            print(met.short_metrics_report())

    # Compute statistics for the last epoch
    interval = idx - WARMUP_STEPS # skip warmup iterations
    throughput = interval / (time.time() - start)
    print("Train throughput (iter/sec): {}".format(throughput))
    print("Final loss is {:0.4f}".format(loss.detach().to('cpu')))

    # Save checkpoint for evaluation
    os.makedirs("checkpoints", exist_ok=True)
    checkpoint = {'state_dict': model.state_dict()}
    
    # XLA: 在 2.24.0 中，xm.save 的使用方式保持不变
    # 但建议先同步所有设备
    xm.wait_device_ops()  # 2.24.0 推荐：确保所有操作完成
    xm.save(checkpoint,'checkpoints/checkpoint.pt')

    print('----------End Training ---------------')
    
    # 2.24.0 新增：最终的指标报告
    print("Final XLA metrics:")
    print(met.short_metrics_report())

if __name__ == '__main__':
    main()
