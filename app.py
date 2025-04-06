import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(layout="wide")
st.title("📈 Price Action vs Buy/Sell Pressure Analysis")

# Sidebar inputs
with st.sidebar:
    ticker = st.text_input("Enter US Stock Ticker:", "AAPL").upper()
    period = st.selectbox("Select data period:", ["1d", "5d", "1mo", "3mo"], index=1)  # Shorter periods for minute data
    interval = st.selectbox("Select interval:", ["1m", "5m", "15m", "1h"], index=0)  # Added 1-minute interval
    show_imbalance = st.checkbox("Show Buy/Sell Imbalance Line", value=True)
    show_cumulative = st.checkbox("Show Cumulative Pressure", value=True)

# Data Fetching and Processing
if ticker:
    data = yf.download(ticker, period=period, interval=interval)

    if data.empty:
        st.error("No data found. Check ticker or interval.")
    else:
        # Basic calculations with proper alignment
        data['Price Change'] = data['Close'].diff()
        data['Volume Delta'] = data['Volume'].diff()
        
        # Replace the volume analysis section with this improved version:
        # Calculate moving averages first
        data['Volume SMA20'] = data['Volume'].rolling(window=20).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()

        # Enhanced pressure calculations with proper Series alignment
        data['Buy Pressure'] = data['Volume'].where(data['Price Change'] > 0, 0)
        data['Sell Pressure'] = data['Volume'].where(data['Price Change'] < 0, 0)
        data['Net Pressure'] = data['Buy Pressure'] - data['Sell Pressure']
        data['Volume_Total'] = data['Buy Pressure'] + data['Sell Pressure']

        # Calculate percentages with safe division
        data['Buy Volume %'] = (data['Buy Pressure'] / data['Volume_Total'] * 100).fillna(0)
        data['Sell Volume %'] = (data['Sell Pressure'] / data['Volume_Total'] * 100).fillna(0)

        # Volume analysis with proper Series alignment
        vol, vol_sma = data['Volume'].align(data['Volume SMA20'], axis=0, join='inner')
        data['Volume_Above_Avg'] = (vol > vol_sma).astype(int)

        _, vol_sma = data['Volume'].align(data['Volume SMA20'], axis=0, join='inner')
        data['Volume_Shock'] = (data['Volume'] > (2 * vol_sma)).astype(int)


        # Calculate final metrics
        data['Imbalance'] = (data['Net Pressure'] / data['Volume_Total'].replace(0, 1)).fillna(0)
        data['Cumulative Pressure'] = data['Net Pressure'].cumsum()
        data['Minute_Return'] = data['Close'].pct_change()

        # Enhanced tooltip
        def create_tooltip(row):
            volume_status = "HIGH" if row['Volume_Above_Avg'] else "normal"
            volume_shock = "🔥" if row['Volume_Shock'] else ""
            return (
                f'Time: {row.name.strftime("%H:%M:%S")}<br>' +
                f'Price: ${float(row["Close"]):.2f} ({float(row["Minute_Return"]*100):.2f}%)<br>' +
                f'Volume: {float(row["Volume"])/1e3:.1f}K {volume_shock}<br>' +
                f'Volume Status: {volume_status}<br>' +
                f'Buy Vol: {float(row["Buy Pressure"])/1e3:.1f}K ({float(row["Buy Volume %"]):.1f}%)<br>' +
                f'Sell Vol: {float(row["Sell Pressure"])/1e3:.1f}K ({float(row["Sell Volume %"]):.1f}%)'
            )

        data['Tooltip'] = data.apply(create_tooltip, axis=1)

        # Create Figure with Secondary Y-axes
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.5, 0.25, 0.25],  # Height ratios for price, volume, and pressure
            vertical_spacing=0.05,
            subplot_titles=[
                f"{ticker} 1-Minute Price Action", 
                "Volume Analysis", 
                "Buy/Sell Pressure"
            ]
        )

        # Price Chart (separate from volume)
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red',
            hovertext=data['Tooltip'],
            hoverinfo='text',
        ), row=1, col=1)

        # Add moving averages to price chart
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA20'],
            name='20-day MA',
            line=dict(color='blue', width=1),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA50'],
            name='50-day MA',
            line=dict(color='orange', width=1),
        ), row=1, col=1)

        # Volume bars in middle subplot
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=['green' if x >= 0 else 'red' for x in data['Price Change']],
            opacity=0.3,
        ), row=2, col=1)

        # Add volume delta visualization
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume Delta'],
            name='Volume Δ',
            marker_color=['green' if x >= 0 else 'red' for x in data['Volume Delta']],
            opacity=0.3
        ), row=2, col=1)

        # Buy/Sell Pressure in bottom subplot
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Buy Pressure'],
            name='Buy Volume',
            marker_color='rgba(0, 255, 0, 0.3)',
            hovertext='Buy: ' + (data['Buy Pressure']/1e6).round(1).astype(str) + 'M (' + 
                      data['Buy Volume %'].astype(str) + '%)',
            hoverinfo='text',
        ), row=3, col=1)

        fig.add_trace(go.Bar(
            x=data.index,
            y=-data['Sell Pressure'],
            name='Sell Volume',
            marker_color='rgba(255, 0, 0, 0.3)',
            hovertext='Sell: ' + (data['Sell Pressure']/1e6).round(1).astype(str) + 'M (' + 
                      data['Sell Volume %'].astype(str) + '%)',
            hoverinfo='text',
        ), row=3, col=1)

        if show_imbalance:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Imbalance'],
                name='Buy/Sell Imbalance',
                line=dict(color='orange', width=1),
            ), row=3, col=1)

        if show_cumulative:
            # Add cumulative pressure line to price chart
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Cumulative Pressure']/data['Cumulative Pressure'].abs().max()*data['Close'].mean(),
                name='Cumulative Pressure',
                line=dict(color='purple', width=1, dash='dot'),
                opacity=0.7
            ), row=1, col=1)

        # Add volume shock indicators
        volume_shocks = data[data['Volume_Shock']]
        if not volume_shocks.empty:
            fig.add_trace(go.Scatter(
                x=volume_shocks.index,
                y=volume_shocks['High'],
                mode='markers',
                name='Volume Spike',
                marker=dict(
                    symbol='triangle-up',
                    size=8,
                    color='yellow',
                    line=dict(color='red', width=1)
                )
            ), row=1, col=1)

        # Update Layout
        fig.update_layout(
            height=1000,  # Increased height for better visibility
            margin=dict(t=30, l=40, r=40, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        # Update y-axes titles and properties
        fig.update_yaxes(title="Price ($)", row=1, col=1)
        fig.update_yaxes(title="Volume", row=2, col=1)
        fig.update_yaxes(title="Pressure", row=3, col=1)

        # Add range buttons
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=30, label="30m", step="minute", stepmode="backward"),
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=3, label="3h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )
        )

        # Show plot
        st.plotly_chart(fig, use_container_width=True)

        # Fix metrics calculation
        try:
            # Calculate metrics using float values
            total_volume = float(data['Volume'].sum())
            buy_volume = float(data['Buy Pressure'].sum())
            sell_volume = float(data['Sell Pressure'].sum())
            
            # Calculate ratios
            buy_ratio = (buy_volume / total_volume * 100) if total_volume > 0 else 0
            sell_ratio = (sell_volume / total_volume * 100) if total_volume > 0 else 0
            net_pressure = buy_ratio - sell_ratio

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Buy Pressure Ratio", f"{buy_ratio:.1f}%")
            with col2:
                st.metric("Sell Pressure Ratio", f"{sell_ratio:.1f}%")
            with col3:
                st.metric("Net Pressure Bias", f"{net_pressure:.1f}%")
        except Exception as e:
            st.warning("Could not calculate metrics due to insufficient data")

        # Daily summary statistics
        st.subheader("Daily Trading Summary")
        last_day = data.index[-1].strftime('%Y-%m-%d')
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Last Trading Day", last_day)
        with col2:
            st.metric("Total Volume", f"{data['Total Volume'][-1]/1e6:.1f}M")
        with col3:
            st.metric("Buy Volume %", f"{data['Buy Volume %'][-1]:.1f}%")
        with col4:
            st.metric("Sell Volume %", f"{data['Sell Volume %'][-1]:.1f}%")

        # Price analysis metrics
        current_price = data['Close'].iloc[-1]
        price_change = data['Close'].pct_change().iloc[-1] * 100
        
        st.subheader("Price Analysis")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            st.metric("Daily Change", f"{price_change:.2f}%")
        with col3:
            st.metric("20-day MA Status", f"{ma20_cross} MA20")
        with col4:
            st.metric("Trading Range", f"${data['High'].max():.2f} - ${data['Low'].min():.2f}")

        # Transaction Analysis
        st.subheader("Transaction Analysis")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_trade_size = data['Total Volume'].mean()
            st.metric("Avg Trade Size", f"{avg_trade_size/1e3:.1f}K")
        
        with col2:
            max_trade = data['Total Volume'].max()
            st.metric("Largest Trade", f"{max_trade/1e3:.1f}K")
        
        with col3:
            buy_trades = (data['Buy Pressure'] > 0).sum()
            total_trades = len(data)
            buy_trade_ratio = (buy_trades / total_trades * 100)
            st.metric("Buy Trades %", f"{buy_trade_ratio:.1f}%")
        
        with col4:
            sell_trades = (data['Sell Pressure'] > 0).sum()
            sell_trade_ratio = (sell_trades / total_trades * 100)
            st.metric("Sell Trades %", f"{sell_trade_ratio:.1f}%")
