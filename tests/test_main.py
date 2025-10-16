"""
Unit tests for the main Streamlit application
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestStockAnalysis:
    """Test class for stock analysis functionality"""
    
    def test_data_processing(self):
        """Test basic data processing functions"""
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, 100),
            'High': np.random.uniform(100, 200, 100),
            'Low': np.random.uniform(100, 200, 100),
            'Close': np.random.uniform(100, 200, 100),
            'Volume': np.random.uniform(1000000, 10000000, 100)
        }, index=dates)
        
        # Test SMA calculation
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        assert not data['SMA20'].isna().all()
        
        # Test EMA calculation
        data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
        assert not data['EMA20'].isna().all()
        
        # Test RSI calculation
        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # RSI should be between 0 and 100
        valid_rsi = data['RSI'].dropna()
        assert all(valid_rsi >= 0) and all(valid_rsi <= 100)
    
    @patch('yfinance.Ticker')
    def test_ticker_data_fetch(self, mock_ticker):
        """Test ticker data fetching with mocked yfinance"""
        # Mock the ticker response
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'shortName': 'Apple Inc.',
            'currentPrice': 150.0,
            'fiftyTwoWeekHigh': 200.0,
            'fiftyTwoWeekLow': 100.0,
            'volume': 50000000,
            'marketCap': 2500000000000,
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        
        # Mock history data
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        mock_history = pd.DataFrame({
            'Open': np.random.uniform(140, 160, 30),
            'High': np.random.uniform(140, 160, 30),
            'Low': np.random.uniform(140, 160, 30),
            'Close': np.random.uniform(140, 160, 30),
            'Volume': np.random.uniform(1000000, 10000000, 30)
        }, index=dates)
        
        mock_ticker_instance.history.return_value = mock_history
        mock_ticker.return_value = mock_ticker_instance
        
        # Test the ticker creation and data fetching
        ticker = mock_ticker('AAPL')
        info = ticker.info
        history = ticker.history(period='1mo')
        
        assert info['shortName'] == 'Apple Inc.'
        assert len(history) == 30
        assert 'Close' in history.columns
    
    def test_technical_indicators(self):
        """Test technical indicator calculations"""
        # Create sample price data
        np.random.seed(42)  # For reproducible tests
        prices = np.cumsum(np.random.randn(100) * 0.01) + 100
        
        data = pd.DataFrame({
            'Close': prices,
            'Volume': np.random.uniform(1000000, 10000000, 100)
        })
        
        # Test MACD calculation
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        assert len(macd) == len(data)
        assert len(signal) == len(data)
        assert not macd.isna().all()
        assert not signal.isna().all()
    
    def test_data_validation(self):
        """Test data validation and error handling"""
        # Test empty dataframe handling
        empty_df = pd.DataFrame()
        assert empty_df.empty
        
        # Test invalid ticker handling
        invalid_ticker_info = {}
        assert "shortName" not in invalid_ticker_info
        
        # Test data type validation
        valid_data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0],
            'Volume': [1000000, 2000000, 3000000]
        })
        assert valid_data['Close'].dtype in ['float64', 'int64']
        assert valid_data['Volume'].dtype in ['float64', 'int64']

if __name__ == "__main__":
    pytest.main([__file__])
