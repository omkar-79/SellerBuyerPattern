import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Snapshot", layout="wide")
st.title("📊 Stock Overview Dashboard")

# Sidebar - Ticker Input
ticker_input = st.sidebar.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA, MSFT):", "AAPL").upper()

# Sidebar - Toggle Sections
st.sidebar.markdown("### 📂 Sections")
show_stats = True  # default always shown
show_chart = st.sidebar.checkbox("Price Chart", value=True)
show_inst = st.sidebar.checkbox("Institutional Holders")
show_maj = st.sidebar.checkbox("Major Holders")
show_ins_tx = st.sidebar.checkbox("Insider Transactions")
show_ins_buy = st.sidebar.checkbox("Insider Purchases")

# Initialize subplots with shared x-axis
fig_combined = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.1,
    row_heights=[0.7, 0.3],
    subplot_titles=("Price Chart with Indicators", "Volume")
)

# Fetch data if ticker entered
if ticker_input:
    try:
        ticker = yf.Ticker(ticker_input)
        info = ticker.info

        if "shortName" not in info:
            st.error("Invalid ticker or data unavailable. Please check the symbol.")
        else:
            st.header(f"📌 {info.get('shortName', ticker_input)} ({ticker_input})")

            # Default Stats Section
            if show_stats:
                st.subheader("📌 Key Statistics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", info.get("currentPrice", "N/A"))
                col1.metric("52 Week High", info.get("fiftyTwoWeekHigh", "N/A"))
                col1.metric("52 Week Low", info.get("fiftyTwoWeekLow", "N/A"))
                col2.metric("Volume", info.get("volume", "N/A"))
                col2.metric("Market Cap", info.get("marketCap", "N/A"))
                col3.metric("Sector", info.get("sector", "N/A"))
                col3.metric("Industry", info.get("industry", "N/A"))

            # Price Chart
            if show_chart:
                st.subheader("📈 Technical Chart Viewer")

                # Select Period and Interval
                period = st.selectbox("Select Period", 
                    ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=2)

                interval = st.selectbox("Select Interval", 
                    ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"], index=2)
                
                # Set dynamic tick format
                if interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m"]:
                    tick_format = "%H:%M"  # Hour:Minute for intraday data
                elif interval in ["1d", "5d"]:
                    tick_format = "%b %d"  # e.g., Apr 06
                else:
                    tick_format = "%Y-%m-%d"  # Full date for long-term view


                # Fetch data
                df = ticker.history(period=period, interval=interval)

                if df.empty:
                    st.warning("No data available for selected period/interval.")
                else:
                    # Calculate indicators (SMA, EMA, RSI, MACD)
                    df['SMA20'] = df['Close'].rolling(window=20).mean()
                    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

                    # RSI Calculation
                    delta = df['Close'].diff()
                    gain = delta.clip(lower=0)
                    loss = -delta.clip(upper=0)
                    avg_gain = gain.rolling(14).mean()
                    avg_loss = loss.rolling(14).mean()
                    rs = avg_gain / avg_loss
                    df['RSI'] = 100 - (100 / (1 + rs))

                    # MACD Calculation
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    df['MACD'] = exp1 - exp2
                    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

                    # Indicator selection
                    indicator = st.selectbox("Select Indicator to Display", ["Price (SMA/EMA)", "RSI", "MACD"])

                    # Initialize a figure
                    fig = go.Figure()

                    # --- Plot Price (SMA/EMA/RSI/MACD) ---
                    if indicator == "Price (SMA/EMA)":
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price', line=dict(color='blue')), row=1, col=1)
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name='SMA 20', line=dict(color='orange')), row=1, col=1)
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA 20', line=dict(color='green')), row=1, col=1)

                    elif indicator == "RSI":
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=1, col=1)
                        fig_combined.add_hline(y=70, line=dict(color='red', dash='dash'), row=1, col=1)
                        fig_combined.add_hline(y=30, line=dict(color='green', dash='dash'), row=1, col=1)

                    elif indicator == "MACD":
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='black')), row=1, col=1)
                        fig_combined.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal Line', line=dict(color='red')), row=1, col=1)


                    
                    # Fetch Volume Data
                    df_hist = ticker.history(period=period, interval=interval)

                    if df_hist.empty:
                        st.warning("No data available for selected period/interval.")
                    else:
                        # Volume Chart with Color-Coding for Buy and Sell
                        st.subheader(f"{ticker_input} Price and Volume Chart")
                        
                        # --- Volume chart ---
                        df_hist['Color'] = df_hist['Close'].diff().apply(lambda x: 'green' if x > 0 else 'red')
                        fig_combined.add_trace(go.Bar(
                            x=df_hist.index, 
                            y=df_hist['Volume'], 
                            marker_color=df_hist['Color'], 
                            name='Volume',
                            showlegend=False
                        ), row=2, col=1)

                        # --- Update layout ---
                        fig_combined.update_layout(
                            height=800,
                            title=f"{ticker_input} Technical Chart and Volume",
                            margin=dict(l=40, r=40, t=60, b=40),
                            xaxis2=dict(title="Date", tickformat=tick_format),
                            yaxis=dict(title="Price"),
                            yaxis2=dict(title="Volume"),
                            hovermode='x unified'
                        )

                        st.plotly_chart(fig_combined, use_container_width=True)

                       



            # Institutional Holders
            if show_inst:
                st.subheader("🏛️ Institutional Holders")
                try:
                    inst = ticker.institutional_holders
                    if inst is not None and not inst.empty:
                        st.dataframe(inst)
                    else:
                        st.info("No institutional holder data available.")
                except Exception as e:
                    st.warning(f"Error fetching institutional holders: {e}")

            # Major Holders
            if show_maj:
                st.subheader("👥 Major Holders")
                try:
                    maj = ticker.major_holders
                    if maj is not None and not maj.empty:
                        if isinstance(maj, pd.DataFrame):
                            st.dataframe(maj)
                        else:
                            st.table(maj.to_frame().rename(columns={0: "Value"}))
                    else:
                        st.info("No major holder data available.")
                except Exception as e:
                    st.warning(f"Error fetching major holders: {e}")

            # Insider Transactions
            if show_ins_tx or show_ins_buy:
                try:
                    ins_tx = ticker.insider_transactions
                except Exception as e:
                    st.warning(f"Error fetching insider transactions: {e}")
                    ins_tx = None

            if show_ins_tx:
                st.subheader("🔄 Insider Transactions")
                if ins_tx is not None and not ins_tx.empty:
                    st.dataframe(ins_tx)
                else:
                    st.info("No insider transactions data available.")

            if show_ins_buy:
                st.subheader("💼 Insider Purchases")
                if ins_tx is not None and not ins_tx.empty:
                    purchases = ins_tx[ins_tx['Transaction'] == 'Buy']
                    if not purchases.empty:
                        st.dataframe(purchases)
                    else:
                        st.info("No insider purchases found.")
                else:
                    st.info("No insider transactions to filter for purchases.")

    except Exception as e:
        st.error(f"Error loading data: {e}")
