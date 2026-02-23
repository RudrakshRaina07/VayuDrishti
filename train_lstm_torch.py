print("🚀 Training CITY-AWARE LSTM model")

import torch
import torch.nn as nn
import numpy as np
import mysql.connector
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
from dotenv import load_dotenv

load_dotenv()

# ================= CONFIG =================
SEQ_LEN = 10
EPOCHS = 20
LR = 0.001
CITY = "Mumbai"   # 🔁 change & retrain per city if needed

# ================= LOAD DATA =================
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    port=3306
)
cur = db.cursor()

cur.execute(
    "SELECT aqi, traffic FROM history WHERE city=%s ORDER BY created_at",
    (CITY,)
)
rows = cur.fetchall()
cur.close()
db.close()

print(f"📊 Rows fetched for {CITY}: {len(rows)}")

if len(rows) < SEQ_LEN + 1:
    raise ValueError("❌ Not enough data to train LSTM")

data = np.array(rows, dtype=np.float32)

# ================= SCALE =================
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)
joblib.dump(scaler, f"scaler_{CITY}.pkl")

# ================= SEQUENCES =================
X, y = [], []
for i in range(len(data_scaled) - SEQ_LEN):
    X.append(data_scaled[i:i + SEQ_LEN])
    y.append(data_scaled[i + SEQ_LEN][0])  # AQI only

X = torch.tensor(np.array(X), dtype=torch.float32)
y = torch.tensor(np.array(y), dtype=torch.float32).view(-1, 1)

# ================= MODEL =================
class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=2, hidden_size=64, batch_first=True)
        self.fc = nn.Linear(64, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

model = LSTMModel()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

# ================= TRAIN =================
for epoch in range(EPOCHS):
    optimizer.zero_grad()
    output = model(X)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {loss.item():.6f}")

# ================= SAVE =================
torch.save(model.state_dict(), f"model_{CITY}.pt")
print(f"✅ LSTM trained and saved for {CITY}")
