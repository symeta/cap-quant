import os
import time
import torch
from model_updated import MLP

from torchvision.datasets import mnist
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor

# XLA imports for Neuron SDK 2.24.0
import torch_xla.core.xla_model as xm
import torch_xla.distributed.parallel_loader as pl
import torch_xla.debug.metrics as met
import torch_xla.amp as xla_amp  # 2.24.0 新增：混合精度支持

# Global constants
EPOCHS = 4
WARMUP_STEPS = 2
BATCH_SIZE = 32
USE_AMP = True  # 启用混合精度训练

# Load MNIST train dataset
train_dataset = mnist.MNIST(root='./MNIST_DATA_train',
                            train=True, download=True, transform=ToTensor())

def main():
    # Prepare data loader
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE)
    
    # XLA: 使用 ParallelLoader (2.24.0 推荐)
    para_loader = pl.ParallelLoader(train_loader, [xm.xla_device()])
    train_loader = para_loader.per_device_loader(xm.xla_device())

    # Fix the random number generator seeds for reproducibility
    torch.manual_seed(0)

    # XLA: 设备指定 (2.24.0)
    device = xm.xla_device()
    print(f"Using device: {device}")

    # Move model to device and declare optimizer and loss function
    model = MLP().to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    loss_fn = torch.nn.NLLLoss()
    
    # 2.24.0 新增：混合精度训练支持
    if USE_AMP:
        scaler = xla_amp.GradScaler()
        print("Using Automatic Mixed Precision (AMP)")

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
            
            if USE_AMP:
                # 混合精度训练 (2.24.0)
                with xla_amp.autocast():
                    output = model(train_x)
                    loss = loss_fn(output, train_label)
                
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                # 标准训练
                output = model(train_x)
                loss = loss_fn(output, train_label)
                loss.backward()
                optimizer.step()
            
            # XLA: mark_step
            xm.mark_step()
            
            if idx < WARMUP_STEPS:
                start = time.time()

        print(f"Epoch {epoch + 1}/{EPOCHS} completed")

    # Compute statistics
    interval = idx - WARMUP_STEPS
    throughput = interval / (time.time() - start)
    print("Train throughput (iter/sec): {}".format(throughput))
    print("Final loss is {:0.4f}".format(loss.detach().to('cpu')))

    # Save checkpoint
    os.makedirs("checkpoints", exist_ok=True)
    checkpoint = {'state_dict': model.state_dict()}
    
    # 确保所有操作完成 (2.24.0 推荐)
    xm.wait_device_ops()
    xm.save(checkpoint,'checkpoints/checkpoint.pt')

    print('----------End Training ---------------')
    print("Final XLA metrics:")
    print(met.short_metrics_report())

if __name__ == '__main__':
    main()
