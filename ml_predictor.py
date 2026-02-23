import os
import torch
import numpy as np
import pandas as pd
import joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import torch.nn as nn

# ================= ENV =================
load_dotenv()

SEQ_LEN = 10
BASE_DIR = os.path.join(os.path.dirname(__file__), "models")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise RuntimeError("Missing DB environment variables")

# ================= DB =================
engine = create_engine(
    URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=DB_NAME,
    )
)

# ================= MODEL ARCH (MUST MATCH TRAINING) =================
class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=2, hidden_size=64, batch_first=True)
        self.fc = nn.Linear(64, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

# ================= LOAD MODEL =================
def load_city_model(city):
    city = city.capitalize()   # Delhi

    model_path = os.path.join(BASE_DIR, f"model_{city}.pt")
    scaler_path = os.path.join(BASE_DIR, f"scaler_{city}.pkl")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        print(f"⚠️ No model for {city}")
        return None, None

    model = LSTMModel()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    scaler = joblib.load(scaler_path)

    print(f"✅ Loaded LSTM + scaler for {city}")
    return model, scaler

# ================= FETCH DATA =================
def fetch_last_records(city):
    df = pd.read_sql(
        """
        SELECT aqi, traffic
        FROM history
        WHERE city = %s
        ORDER BY id DESC
        LIMIT %s
        """,
        engine,
        params=(city, SEQ_LEN)
    )

    if len(df) < SEQ_LEN:
        return None

    return df.iloc[::-1].values

# ================= PREDICT =================
def predict_future(city):
    try:
        data = fetch_last_records(city)
        if data is None:
            return None

        model, scaler = load_city_model(city)
        if model is None:
            return None

        data_scaled = scaler.transform(data)
        seq = torch.tensor(data_scaled, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            pred = model(seq).item()

        return round(pred, 2)

    except Exception as e:
        print("❌ Prediction error:", e)
        return None
