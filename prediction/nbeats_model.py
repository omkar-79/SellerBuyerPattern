import os
import requests
import pandas as pd
import numpy as np
import torch
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from torch import nn
import pytorch_lightning as pl
from dotenv import load_dotenv
from pytorch_lightning import Trainer
from sklearn.preprocessing import StandardScaler

# Load API Key
load_dotenv()
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# --- Fetch Alpha Vantage 1-hour data ---
@st.cache_data
def fetch_alpha_vantage_hourly(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": "60min",
        "outputsize": "full",
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "Time Series (60min)" not in data:
        st.error(f"Error fetching data: {data.get('Note') or data}")
        return None

    df = pd.DataFrame.from_dict(data["Time Series (60min)"], orient='index', dtype='float')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'datetime'}, inplace=True)
    return df

# --- Feature Engineering ---
def add_buy_sell_volume(df):
    df['Price Change'] = df['Close'].diff()
    df['Buy Volume'] = np.where(df['Price Change'] > 0, df['Volume'], 0)
    df['Sell Volume'] = np.where(df['Price Change'] < 0, df['Volume'], 0)
    df.fillna(0, inplace=True)
    return df

# --- Create lagged features ---
def create_lag_features(df, lags=5):
    for i in range(1, lags + 1):
        df[f'Close_lag_{i}'] = df['Close'].shift(i)
        df[f'Buy_lag_{i}'] = df['Buy Volume'].shift(i)
        df[f'Sell_lag_{i}'] = df['Sell Volume'].shift(i)
    df.dropna(inplace=True)
    return df

# --- Custom LSTM model ---
class LSTMRegressor(pl.LightningModule):
    def __init__(self, input_size, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, 1)
        self.loss_fn = nn.MSELoss()

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.linear(out[:, -1, :])

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = self.loss_fn(y_hat.squeeze(), y)
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# --- Streamlit UI ---
st.set_page_config(page_title="LSTM Price Predictor", layout="wide")
st.title("📈 Predict Close Price Using Buy/Sell Volume + LSTM")

ticker = st.text_input("Enter Stock Ticker (e.g. AAPL, TSLA):", value="AAPL")
lags = st.slider("Number of Lag Steps", 1, 10, 5)

if st.button("Train and Predict"):
    df = fetch_alpha_vantage_hourly(ticker)
    if df is not None:
        df = add_buy_sell_volume(df)
        df = create_lag_features(df, lags)

        feature_cols = [col for col in df.columns if 'lag' in col]
        target_col = 'Close'

        # Normalize features and target
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()

        X_scaled = scaler_X.fit_transform(df[feature_cols].values)
        y_scaled = scaler_y.fit_transform(df[[target_col]].values).flatten()

        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y_scaled[:split_idx], y_scaled[split_idx:]

        X_train = torch.tensor(X_train, dtype=torch.float32).unsqueeze(1)
        y_train = torch.tensor(y_train, dtype=torch.float32)
        X_test = torch.tensor(X_test, dtype=torch.float32).unsqueeze(1)
        y_test = torch.tensor(y_test, dtype=torch.float32)

        train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64)

        model = LSTMRegressor(input_size=X_train.shape[2])
        trainer = Trainer(max_epochs=10, accelerator="auto", logger=False)
        trainer.fit(model, train_loader)

        # --- Inference ---
        model.eval()
        with torch.no_grad():
            preds_scaled = model(X_test).squeeze().numpy()
            preds = scaler_y.inverse_transform(preds_scaled.reshape(-1, 1)).flatten()
            y_actual = scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()

        # --- Plot ---
        index = df.iloc[split_idx:].datetime.values
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(index, y_actual, label="Actual")
        ax.plot(index, preds, label="Predicted", linestyle="--")
        ax.set_title(f"{ticker} - Predicted vs Actual Close Price")
        ax.set_xlabel("Time")
        ax.set_ylabel("Close Price")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # --- Metrics ---
        rmse = np.sqrt(np.mean((preds - y_actual) ** 2))
        st.metric("RMSE", f"{rmse:.2f}")
