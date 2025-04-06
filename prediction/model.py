import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import plotly.graph_objects as go

st.set_page_config(page_title="📈 Stock Price Prediction", layout="wide")
st.title("📈 Predict Next Close Price (Based on Buy/Sell Volume)")

# --- Fetch historical data ---
@st.cache_data
def fetch_full_hourly_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="730d", interval="60m")
    df = df[~df.index.duplicated(keep='first')]
    df.dropna(inplace=True)
    return df


# --- Feature engineering ---
def add_buy_sell_features(df):
    df['Price Change'] = df['Close'].diff()
    df['Buy Volume'] = np.where(df['Price Change'] > 0, df['Volume'], 0)
    df['Sell Volume'] = np.where(df['Price Change'] < 0, df['Volume'], 0)
    df.fillna(0, inplace=True)
    return df

# --- Create lag features ---
def create_lag_features(df, lags=3):
    for i in range(1, lags + 1):
        df[f'Buy_lag_{i}'] = df['Buy Volume'].shift(i)
        df[f'Sell_lag_{i}'] = df['Sell Volume'].shift(i)
        df[f'Close_lag_{i}'] = df['Close'].shift(i)
    df.dropna(inplace=True)
    return df

# --- Train model ---
def train_model(df, test_start="2025-03-31", test_end="2025-04-05"):
    features = [col for col in df.columns if 'lag' in col]
    X = df[features]
    y = df['Close']

    X_train = X[df.index < test_start]
    y_train = y[df.index < test_start]
    X_test = X[(df.index >= test_start) & (df.index <= test_end)]
    y_test = y[(df.index >= test_start) & (df.index <= test_end)]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return model, X_test, y_test, y_pred



# --- Sidebar ---
ticker = st.sidebar.text_input("Enter Stock Ticker:", value="AAPL").upper()
lags = st.sidebar.slider("Lag Periods", 1, 10, 3)

# --- Run prediction pipeline ---
if ticker:
    df = fetch_full_hourly_data(ticker)

    df = add_buy_sell_features(df)
    df = create_lag_features(df, lags=lags)

    model, X_test, y_test, y_pred = train_model(df)

    # --- Metrics ---
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    st.metric("📉 RMSE (Prediction Error)", f"{rmse:.4f}")

    # --- Combine for plotting ---
    df_plot = pd.DataFrame({
        "Actual": y_test.values,
        "Predicted": y_pred
    }, index=y_test.index)

    # --- Plotly chart ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["Actual"], mode='lines+markers', name="Actual"))
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["Predicted"], mode='lines+markers', name="Predicted"))
    fig.update_layout(
        title=f"{ticker} Close Price Prediction",
        xaxis_title="Timestamp",
        yaxis_title="Close Price",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    # --- Data preview ---
    with st.expander("🔍 View Raw Data"):
        st.dataframe(df_plot)

    # --- Option to download ---
    csv = df_plot.to_csv().encode("utf-8")
    st.download_button("📥 Download Predictions CSV", csv, f"{ticker}_predictions.csv", "text/csv")
