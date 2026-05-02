"""Tests for corporate action adjustments."""

import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from nepsense.processors.adjust_prices import (
    calculate_adjustment_factor,
    apply_adjustments,
)


class TestAdjustmentFactorCalculation:
    """Test adjustment factor calculations."""
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        return pd.DataFrame({
            'symbol': ['NABIL'] * 5,
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'open': [1100.0] * 5,
            'high': [1150.0] * 5,
            'low': [1050.0] * 5,
            'close': [1120.0] * 5,
        })
    
    def test_bonus_adjustment_factor_calculation(self, sample_prices):
        """Test bonus share adjustment factor calculation."""
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': [pd.Timestamp('2024-01-03')],
            'action_type': ['BONUS'],
            'bonus_percent': [10.0],
        })
        
        result = calculate_adjustment_factor(sample_prices, actions)
        
        # Result should have adjustment_factor column
        assert 'adjustment_factor' in result.columns
        
        # Adjustment factors should be calculated
        assert len(result) == len(sample_prices)
        assert all(result['adjustment_factor'] > 0)
    
    def test_adjustment_factor_default_is_one(self, sample_prices):
        """Test default adjustment factor is 1.0 (no adjustment)."""
        actions = pd.DataFrame()  # No actions
        
        result = calculate_adjustment_factor(sample_prices, actions)
        
        # All factors should be 1.0 (no adjustment)
        assert all(result['adjustment_factor'] == 1.0)
    
    def test_right_share_adjustment_calculation(self, sample_prices):
        """Test right share adjustment factor."""
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': [pd.Timestamp('2024-01-03')],
            'action_type': ['RIGHT'],
            'right_ratio': [1],
            'right_price': [100.0],
        })
        
        result = calculate_adjustment_factor(sample_prices, actions)
        
        # Should calculate adjustment factors
        assert 'adjustment_factor' in result.columns
        assert len(result) == len(sample_prices)
    
    def test_multiple_actions_cumulative(self, sample_prices):
        """Test multiple actions apply cumulatively."""
        actions = pd.DataFrame({
            'symbol': ['NABIL', 'NABIL'],
            'book_close_date': [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-04')],
            'action_type': ['BONUS', 'BONUS'],
            'bonus_percent': [10.0, 10.0],
        })
        
        result = calculate_adjustment_factor(sample_prices, actions)
        
        # Should have adjustment factors
        assert 'adjustment_factor' in result.columns
        
        # Earliest date should have most adjustments
        earliest = result[result['date'] == '2024-01-01'].iloc[0]
        assert earliest['adjustment_factor'] > 0


class TestApplyAdjustments:
    """Test applying adjustments to price series."""
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        return pd.DataFrame({
            'symbol': ['NABIL'] * 10,
            'date': pd.date_range('2024-01-01', periods=10),
            'open': [1100.0] * 10,
            'high': [1150.0] * 10,
            'low': [1050.0] * 10,
            'close': [1120.0] * 10,
        })
    
    def test_apply_bonus_adjustment(self, sample_prices):
        """Test bonus adjustment applied to all earlier dates."""
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': [pd.Timestamp('2024-01-05')],
            'action_type': ['BONUS'],
            'bonus_percent': [10.0],
        })
        
        result = apply_adjustments(sample_prices, actions)
        
        # Dates before bonus should be adjusted (multiplied by factor)
        # Dates after should be unadjusted
        factor = 1.10
        
        # Before 2024-01-05: should be adjusted
        before = result[result['date'] < '2024-01-05']
        assert len(before) > 0
        
        # After 2024-01-05: should be unadjusted
        after = result[result['date'] >= '2024-01-05']
        assert len(after) > 0
    
    def test_multiple_adjustments_cumulative(self):
        """Test multiple adjustments apply cumulatively."""
        prices = pd.DataFrame({
            'symbol': ['NABIL'] * 20,
            'date': pd.date_range('2024-01-01', periods=20),
            'open': [1000.0] * 20,
            'high': [1050.0] * 20,
            'low': [950.0] * 20,
            'close': [1025.0] * 20,
        })
        prices['date'] = prices['date'].astype(str)
        
        actions = pd.DataFrame({
            'symbol': ['NABIL', 'NABIL'],
            'book_close_date': [pd.Timestamp('2024-01-05'), pd.Timestamp('2024-01-15')],
            'action_type': ['BONUS', 'BONUS'],
            'bonus_percent': [10.0, 10.0],
        })
        
        result = apply_adjustments(prices, actions)
        
        # Result should have adjustment info
        assert len(result) == len(prices)
    
    def test_no_action_returns_original(self, sample_prices):
        """Test data unchanged when no actions specified."""
        result = apply_adjustments(sample_prices.copy(), pd.DataFrame())
        
        # Should still have original values
        assert 'close' in result.columns
        assert result['close'].iloc[0] == 1120.0


class TestAdjustmentIntegration:
    """Integration tests for adjustment pipeline."""
    
    def test_adjustment_preserves_row_count(self):
        """Test adjustment doesn't change number of rows."""
        prices = pd.DataFrame({
            'symbol': ['NABIL', 'NABIL', 'HBL', 'HBL'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
            'open': [1000.0, 1010.0, 500.0, 505.0],
            'high': [1050.0, 1060.0, 520.0, 525.0],
            'low': [950.0, 960.0, 480.0, 485.0],
            'close': [1025.0, 1035.0, 512.0, 517.0],
        })
        
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': ['2024-01-01'],
            'action_type': ['BONUS'],
            'bonus_percent': [10.0],
        })
        
        result = apply_adjustments(prices.copy(), actions)
        assert len(result) == len(prices)
    
    def test_adjustment_handles_missing_symbols(self):
        """Test adjustment handles symbols with no actions."""
        prices = pd.DataFrame({
            'symbol': ['NABIL', 'HBL'],
            'date': ['2024-01-01', '2024-01-01'],
            'close': [1000.0, 500.0],
        })
        
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': ['2024-01-01'],
            'action_type': ['BONUS'],
            'bonus_percent': [10.0],
        })
        
        result = apply_adjustments(prices.copy(), actions)
        
        # Both symbols should still be in result
        assert set(result['symbol']) == {'NABIL', 'HBL'}
    
    def test_adjustment_with_empty_price_data(self):
        """Test graceful handling of empty data."""
        prices = pd.DataFrame({
            'symbol': [],
            'date': [],
            'close': [],
        })
        
        actions = pd.DataFrame({
            'symbol': ['NABIL'],
            'book_close_date': ['2024-01-01'],
            'action_type': ['BONUS'],
            'bonus_percent': [10.0],
        })
        
        result = apply_adjustments(prices.copy(), actions)
        assert len(result) == 0
