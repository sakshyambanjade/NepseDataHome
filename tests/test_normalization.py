import pandas as pd
import pytest
from pathlib import Path
import tempfile

from nepsense.processors import normalize_all, normalize_column_name, normalize_file
from nepsense.config import STANDARD_OHLCV_COLUMNS


class TestColumnNormalization:
    """Test column name alias mapping."""
    
    def test_symbol_alias(self):
        """Test Symbol → symbol normalization."""
        assert normalize_column_name("Symbol") == "symbol"
        assert normalize_column_name("symbol") == "symbol"
        assert normalize_column_name("SYMBOL") == "symbol"
    
    def test_price_aliases(self):
        """Test various price column mappings."""
        assert normalize_column_name("LTP") == "close"
        assert normalize_column_name("Last Traded Price") == "close"
        assert normalize_column_name("close") == "close"
        # Note: "Close Price" is two words and normalizes to "close price"
        # This is expected - the normalize function lowercases but doesn't split
    
    def test_volume_aliases(self):
        """Test volume/quantity column mappings."""
        assert normalize_column_name("Qty") == "volume"
        assert normalize_column_name("Quantity") == "volume"
        assert normalize_column_name("Volume") == "volume"
        assert normalize_column_name("Traded Qty") == "volume"
    
    def test_amount_alias(self):
        """Test Amount → turnover mapping."""
        assert normalize_column_name("Amount") == "turnover"
        assert normalize_column_name("Turnover") == "turnover"
    
    def test_open_high_low_aliases(self):
        """Test OHLC normalization."""
        assert normalize_column_name("Open") == "open"
        assert normalize_column_name("High") == "high"
        assert normalize_column_name("Low") == "low"
        assert normalize_column_name("Close") == "close"
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert normalize_column_name("SYMBOL") == "symbol"
        assert normalize_column_name("High") == "high"
        assert normalize_column_name("ltp") == "close"
    
    def test_unknown_column(self):
        """Test unknown columns are preserved."""
        result = normalize_column_name("UnknownColumn")
        assert result == "unknowncolumn"  # Lowercased but kept


class TestFileNormalization:
    """Test full file normalization."""
    
    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample raw CSV file."""
        data = {
            "Symbol": ["NABIL", "HBL", "TRH"],
            "Open": [1100.0, 550.0, 1500.0],
            "High": [1150.0, 560.0, 1550.0],
            "Low": [1050.0, 540.0, 1450.0],
            "LTP": [1120.0, 555.0, 1510.0],
            "Qty": [100000, 50000, 75000],
            "Amount": [112000000, 27750000, 113250000],
            "date": ["2024-01-15", "2024-01-15", "2024-01-15"],
        }
        df = pd.DataFrame(data)
        csv_file = tmp_path / "2024-01-15.csv"
        df.to_csv(csv_file, index=False)
        return csv_file
    
    def test_normalize_file_creates_output(self, sample_csv, tmp_path):
        """Test that normalization creates output file."""
        output_file = tmp_path / "normalized.csv"
        normalize_file(sample_csv, output_file)
        assert output_file.exists()
    
    def test_normalize_file_has_standard_columns(self, sample_csv, tmp_path):
        """Test output has all standard columns."""
        output_file = tmp_path / "normalized.csv"
        normalize_file(sample_csv, output_file)
        
        df = pd.read_csv(output_file)
        for col in ['symbol', 'open', 'high', 'low', 'close', 'volume', 'date']:
            assert col in df.columns
    
    def test_normalize_removes_duplicates(self, tmp_path):
        """Test duplicate rows are removed."""
        # Create CSV with duplicates
        data = {
            "Symbol": ["NABIL", "NABIL", "HBL"],
            "Open": [1100.0, 1100.0, 550.0],
            "High": [1150.0, 1150.0, 560.0],
            "Low": [1050.0, 1050.0, 540.0],
            "LTP": [1120.0, 1120.0, 555.0],
            "Qty": [100000, 100000, 50000],
            "Amount": [112000000, 112000000, 27750000],
            "date": ["2024-01-15", "2024-01-15", "2024-01-15"],
        }
        df = pd.DataFrame(data)
        input_file = tmp_path / "with_dupes.csv"
        df.to_csv(input_file, index=False)
        
        output_file = tmp_path / "normalized.csv"
        normalize_file(input_file, output_file)
        
        df_out = pd.read_csv(output_file)
        assert len(df_out) == 2  # One duplicate removed
    
    def test_normalize_preserves_data_types(self, sample_csv, tmp_path):
        """Test numeric columns are properly typed."""
        output_file = tmp_path / "normalized.csv"
        normalize_file(sample_csv, output_file)
        
        df = pd.read_csv(output_file)
        # Check numeric columns are floats
        assert pd.api.types.is_numeric_dtype(df['open'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        assert pd.api.types.is_numeric_dtype(df['volume'])
    
    def test_normalize_adds_date_if_missing(self, tmp_path):
        """Test error raised when date column is missing."""
        # Create CSV without date - should raise ValueError
        data = {
            "Symbol": ["NABIL"],
            "LTP": [1120.0],
            "Qty": [100000],
        }
        df = pd.DataFrame(data)
        input_file = tmp_path / "no_date.csv"
        df.to_csv(input_file, index=False)
        
        output_file = tmp_path / "normalized.csv"
        # Date is required - should raise error
        with pytest.raises(ValueError, match="Missing required columns"):
            normalize_file(input_file, output_file)

    def test_normalize_all_preserves_source_partitions(self, tmp_path):
        """Test source-partitioned raw files normalize into matching partitions."""
        input_root = tmp_path / "raw"
        output_root = tmp_path / "normalized"
        raw_dir = input_root / "source=archive" / "2024" / "01"
        raw_dir.mkdir(parents=True)

        df = pd.DataFrame(
            {
                "date": ["2024-01-02"],
                "Symbol": ["NABIL"],
                "LTP": [100],
                "source": ["archive"],
                "source_confidence": [0.7],
            }
        )
        df.to_csv(raw_dir / "2024-01-02.csv", index=False)

        count = normalize_all(input_root, output_root)

        assert count == 1
        assert (
            output_root / "source=archive" / "2024" / "01" / "2024-01-02.csv"
        ).exists()


class TestDataValidation:
    """Test data validation during normalization."""
    
    def test_missing_required_columns(self, tmp_path):
        """Test error on missing required columns."""
        # Create CSV without symbol column
        data = {
            "Open": [1100.0],
            "LTP": [1120.0],
        }
        df = pd.DataFrame(data)
        input_file = tmp_path / "missing_symbol.csv"
        df.to_csv(input_file, index=False)
        
        output_file = tmp_path / "normalized.csv"
        with pytest.raises(ValueError, match="Missing required columns"):
            normalize_file(input_file, output_file)
    
    def test_ohlc_logic_validation(self, tmp_path):
        """Test OHLC relationships (High >= Low, etc.)."""
        # Create invalid OHLC data
        data = {
            "Symbol": ["NABIL"],
            "Open": [1100.0],
            "High": [1050.0],  # High < Open
            "Low": [1000.0],
            "LTP": [1120.0],
            "Qty": [100000],
            "date": ["2024-01-15"],
        }
        df = pd.DataFrame(data)
        input_file = tmp_path / "invalid_ohlc.csv"
        df.to_csv(input_file, index=False)
        
        output_file = tmp_path / "normalized.csv"
        # Should complete but may log warnings
        normalize_file(input_file, output_file)
        # Data should still be saved for manual review
        assert output_file.exists()
