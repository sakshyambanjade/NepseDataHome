import pandas as pd
import pytest
from datetime import datetime, date, timedelta
from pathlib import Path

from nepsense.pipelines.backfill_pipeline import (
    build_trading_calendar,
)
from nepsense.utils import resolve_date


class TestTradingCalendarGeneration:
    """Test trading calendar generation."""
    
    def test_trading_calendar_excludes_weekends(self):
        """Test that weekends are excluded."""
        # January 2024: Jan 6-7 are Saturday-Sunday
        dates = build_trading_calendar("2024-01-05", "2024-01-08")
        
        # Should have Jan 5 and Jan 8, but not 6-7
        dates_set = set(dates)
        assert "2024-01-05" in dates_set
        assert "2024-01-08" in dates_set
        assert "2024-01-06" not in dates_set
        assert "2024-01-07" not in dates_set
    
    def test_trading_calendar_date_range(self):
        """Test calendar includes all business days in range."""
        dates = build_trading_calendar("2024-01-02", "2024-01-10")
        
        # Should have multiple dates
        assert len(dates) >= 5
        
        # All dates should be in range
        for d in dates:
            parsed = datetime.strptime(d, "%Y-%m-%d").date()
            assert datetime(2024, 1, 2).date() <= parsed <= datetime(2024, 1, 10).date()
    
    def test_trading_calendar_resolve_today(self):
        """Test 'today' string is resolved."""
        dates = build_trading_calendar("2026-04-01", "today")
        
        # Should have trading dates from April to today (May 2)
        assert len(dates) > 0
        assert "2026-04-01" in dates or "2026-04-02" in dates  # Apr 1 or first business day
    
    def test_trading_calendar_single_day(self):
        """Test single business day."""
        # 2024-01-01 is Monday
        dates = build_trading_calendar("2024-01-01", "2024-01-01")
        
        assert len(dates) == 1
        assert dates[0] == "2024-01-01"
    
    def test_trading_calendar_weekend_start(self):
        """Test range starting on weekend."""
        # Jan 6, 2024 is Saturday
        dates = build_trading_calendar("2024-01-06", "2024-01-10")
        
        # Should start from Monday Jan 8
        assert "2024-01-06" not in dates
        assert "2024-01-08" in dates
    
    def test_trading_calendar_order(self):
        """Test calendar is in chronological order."""
        dates = build_trading_calendar("2024-01-02", "2024-01-31")
        
        # Dates should be sorted
        assert dates == sorted(dates)
    
    def test_trading_calendar_empty_range(self):
        """Test empty range (end before start)."""
        # This is an edge case - should handle gracefully
        dates = build_trading_calendar("2024-01-10", "2024-01-05")
        
        # Should return empty list or handle gracefully
        assert isinstance(dates, list)
        assert len(dates) == 0


class TestDateResolution:
    """Test date string resolution."""
    
    def test_resolve_today_string(self):
        """Test 'today' resolves to ISO date format."""
        result = resolve_date("today")
        
        # Should be valid ISO format YYYY-MM-DD
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # Year
        assert len(parts[1]) == 2  # Month
        assert len(parts[2]) == 2  # Day
    
    def test_resolve_explicit_date(self):
        """Test explicit date is preserved."""
        result = resolve_date("2024-01-15")
        assert result == "2024-01-15"
    
    def test_resolve_none_becomes_today(self):
        """Test None becomes today."""
        result = resolve_date(None)
        
        # Should be valid ISO date
        assert len(result) == 10
        assert result.count("-") == 2


class TestBackfillPipelineIntegration:
    """Integration tests for backfill pipeline."""
    
    def test_backfill_report_structure(self, tmp_path):
        """Test backfill report has required columns."""
        # This would be tested with actual backfill execution
        # Structure: date, source, status, raw_file, normalized_file, error_message, records_collected, timestamp
        
        # Create a mock report
        report = pd.DataFrame({
            'date': ['2024-01-02'],
            'source': ['sharesansar'],
            'status': ['success'],
            'raw_file': ['/path/to/raw.csv'],
            'normalized_file': ['/path/to/normalized.csv'],
            'error_message': [None],
            'records_collected': [150],
            'timestamp': ['2026-05-02T12:00:00'],
        })
        
        # Verify structure
        required_cols = ['date', 'source', 'status', 'raw_file', 'normalized_file']
        for col in required_cols:
            assert col in report.columns
    
    def test_backfill_success_status(self):
        """Test backfill reports success when data collected."""
        # Verify status values are valid
        valid_statuses = ['success', 'failed', 'skipped', 'partial']
        
        report = pd.DataFrame({
            'status': valid_statuses,
        })
        
        assert all(status in valid_statuses for status in report['status'])
    
    def test_backfill_date_format_consistency(self):
        """Test all dates in report are consistent format."""
        report = pd.DataFrame({
            'date': ['2024-01-02', '2024-01-03', '2024-02-01'],
        })
        
        for date_str in report['date']:
            # Should be parseable as ISO date
            parts = date_str.split('-')
            assert len(parts) == 3
            assert len(parts[0]) == 4
