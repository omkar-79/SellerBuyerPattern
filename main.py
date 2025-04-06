import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

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

            # Price Chart Section
            if show_chart:
                st.subheader("📈 Price Chart")

                period = st.selectbox("Select Period", 
                    ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=2)

                interval = st.selectbox("Select Interval", 
                    ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"], index=2)

                df_hist = ticker.history(period=period, interval=interval)

                if df_hist.empty:
                    st.warning("No data available for selected period/interval.")
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['Close'], mode='lines', name='Close Price'))
                    fig.update_layout(title=f"{ticker_input} Price Over Time", xaxis_title='Date', yaxis_title='Price',
                                      height=400, margin=dict(l=40, r=40, t=40, b=40))
                    st.plotly_chart(fig, use_container_width=True)

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
