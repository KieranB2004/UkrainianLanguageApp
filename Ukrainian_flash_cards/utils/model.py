import torch
import torch.nn as nn
import torch.optim as optim
import os

MODEL_PATH = "data/model.pt"

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(3, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.fc(x)

model = Net()

def load():
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH))

def save():
    torch.save(model.state_dict(), MODEL_PATH)

def predict(c, w, t):
    with torch.no_grad():
        x = torch.tensor([[c, w, t]], dtype=torch.float32)
        return model(x).item()

def train(samples):
    if len(samples) < 10:
        return
    opt = optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    for _ in range(50):
        for c, w, t, y in samples:
            x = torch.tensor([[c, w, t]], dtype=torch.float32)
            target = torch.tensor([[y]], dtype=torch.float32)

            pred = model(x)
            loss = loss_fn(pred, target)

            opt.zero_grad()
            loss.backward()
            opt.step()

    save()