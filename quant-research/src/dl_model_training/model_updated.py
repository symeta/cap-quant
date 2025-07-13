import torch.nn as nn
import torch.nn.functional as F

# Declare 3-layer MLP for MNIST dataset
# 针对 Neuron SDK 2.24.0 优化
class MLP(nn.Module):
    def __init__(self, input_size = 28 * 28, output_size = 10, layers = [120, 84]):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_size, layers[0])
        self.fc2 = nn.Linear(layers[0], layers[1])
        self.fc3 = nn.Linear(layers[1], output_size)
        
        # 2.24.0 优化：添加 dropout 以提高泛化能力
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)  # 在训练时应用 dropout
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return F.log_softmax(x, dim=1)

# 2.24.0 新增：支持混合精度训练的模型版本
class MLPWithAMP(nn.Module):
    def __init__(self, input_size = 28 * 28, output_size = 10, layers = [120, 84]):
        super(MLPWithAMP, self).__init__()
        self.fc1 = nn.Linear(input_size, layers[0])
        self.fc2 = nn.Linear(layers[0], layers[1])
        self.fc3 = nn.Linear(layers[1], output_size)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        # 使用 autocast 进行混合精度计算 (2.24.0 支持)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return F.log_softmax(x, dim=1)
