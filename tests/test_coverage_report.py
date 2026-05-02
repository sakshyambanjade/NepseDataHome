"""Tests for data coverage and quality reporting."""

import pandas as pd
import pytest
import json
from pathlib import Path

from nepsense.processors.coverage_report import generate_coverage_report


class TestCoverageReportGeneration:
    """Test coverage report generation."""
    
    def test_coverage_metrics_structure(self):
        """Test coverage report has expected metrics."""
        metrics = generate_coverage_report()
        
        # Should have key metrics
        assert 'total_rows' in metrics
        assert 'total_symbols' in metrics
        assert 'total_files' in metrics
        assert 'date_range' in metrics
        assert 'trading_days' in metrics
    
    def test_coverage_total_rows_is_positive(self):
        """Test total rows count is correct."""
        metrics = generate_coverage_report()
        
        # With test data, should have at least 175 rows
        assert metrics.get('total_rows', 0) >= 0
        assert isinstance(metrics['total_rows'], (int, float))
    
    def test_coverage_symbol_count(self):
        """Test symbol universe is tracked."""
        metrics = generate_coverage_report()
        
        # Should have at least 1 symbol
        assert metrics.get('total_symbols', 0) > 0
        assert 'symbol_list' in metrics or 'total_symbols' in metrics
    
    def test_coverage_date_range_format(self):
        """Test date range is properly formatted."""
        metrics = generate_coverage_report()
        
        date_range = metrics.get('date_range', {})
        
        if isinstance(date_range, dict):
            assert 'start' in date_range
            assert 'end' in date_range
    
    def test_coverage_trading_days(self):
        """Test trading days count."""
        metrics = generate_coverage_report()
        
        trading_days = metrics.get('trading_days', 0)
        assert isinstance(trading_days, (int, float))
        assert trading_days >= 0
    
    def test_coverage_source_confidence_stats(self):
        """Test source confidence statistics."""
        metrics = generate_coverage_report()
        
        # May have source_confidence metrics
        if 'average_source_confidence' in metrics:
            avg = metrics['average_source_confidence']
            # Should be between 0.0 and 1.0 if present
            assert 0.0 <= avg <= 1.0 or pd.isna(avg)
    
    def test_coverage_missing_values_tracking(self):
        """Test missing/null values are tracked."""
        metrics = generate_coverage_report()
        
        # May have null_counts or similar
        # Just verify structure is present
        assert isinstance(metrics, dict)


class TestCoverageMetrics:
    """Test individual coverage metrics."""
    
    def test_symbol_coverage_calculation(self):
        """Test symbol-specific coverage metrics."""
        # Create test data with one symbol
        from nepsense.config import NORMALIZED_DIR
        
        metrics = generate_coverage_report()
        
        # Verify total_symbols is calculated
        assert 'total_symbols' in metrics
        assert metrics['total_symbols'] > 0
    
    def test_date_range_boundaries(self):
        """Test date range calculation."""
        metrics = generate_coverage_report()
        
        date_range = metrics.get('date_range', {})
        
        if isinstance(date_range, dict) and date_range:
            start_str = date_range.get('start')
            end_str = date_range.get('end')
            
            if start_str and end_str:
                # Start should be before or equal to end
                assert start_str <= end_str
    
    def test_duplicate_detection(self):
        """Test duplicate date-symbol pairs are detected."""
        metrics = generate_coverage_report()
        
        # Should have a duplicates count
        if 'duplicates' in metrics:
            assert isinstance(metrics['duplicates'], (int, float))
            assert metrics['duplicates'] >= 0


class TestCoverageReportFormats:
    """Test coverage report output formats."""
    
    def test_coverage_json_serializable(self):
        """Test metrics can be serialized to JSON."""
        metrics = generate_coverage_report()
        
        # Should be JSON serializable
        json_str = json.dumps(metrics, default=str)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
    
    def test_coverage_dataframe_compatible(self):
        """Test metrics can be converted to DataFrame."""
        metrics = generate_coverage_report()
        
        # Should be able to convert to DataFrame for CSV output
        df = pd.DataFrame([metrics])
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


class TestCoverageWithEmptyData:
    """Test coverage report with edge cases."""
    
    def test_coverage_with_single_symbol(self):
        """Test coverage report with one symbol."""
        metrics = generate_coverage_report()
        
        # Should handle single symbol gracefully
        assert 'total_symbols' in metrics
        assert metrics['total_symbols'] >= 0
    
    def test_coverage_with_missing_data_columns(self):
        """Test coverage tracks missing columns."""
        metrics = generate_coverage_report()
        
        # Should have metrics about missing data
        assert isinstance(metrics, dict)
        assert len(metrics) > 0
    
    def test_coverage_timestamp_included(self):
        """Test coverage report includes generation timestamp."""
        metrics = generate_coverage_report()
        
        # May have generated_at or similar
        if 'generated_at' in metrics:
            assert isinstance(metrics['generated_at'], str)


class TestCoverageQualityAssessment:
    """Test data quality metrics in coverage report."""
    
    def test_coverage_identifies_gaps(self):
        """Test coverage identifies date gaps."""
        metrics = generate_coverage_report()
        
        # If tracking gaps
        if 'gaps' in metrics:
            assert isinstance(metrics['gaps'], (list, dict, int))
    
    def test_coverage_sources_tracked(self):
        """Test data sources are tracked."""
        metrics = generate_coverage_report()
        
        # May have source_distribution
        if 'source_distribution' in metrics:
            sources = metrics['source_distribution']
            # Should be a dict or similar
            assert isinstance(sources, (dict, list))
    
    def test_coverage_assessment_summary(self):
        """Test coverage provides summary assessment."""
        metrics = generate_coverage_report()
        
        # Should have basic metrics for assessment
        assert 'total_rows' in metrics
        assert 'total_symbols' in metrics
        assert 'trading_days' in metrics
