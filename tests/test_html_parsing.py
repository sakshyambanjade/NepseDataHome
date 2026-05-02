"""Test HTML table parsing improvements."""

import pandas as pd

from nepsense.collectors import _parse_table_with_bs4, _choose_market_table


class TestHTMLTableParsing:
    """Test improved HTML table parsing with BeautifulSoup."""
    
    def test_parse_simple_table(self):
        """Test parsing a simple well-formed HTML table."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Volume</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>NABIL</td>
                    <td>1,200.00</td>
                    <td>10,000</td>
                </tr>
                <tr>
                    <td>HBL</td>
                    <td>800.00</td>
                    <td>5,000</td>
                </tr>
            </tbody>
        </table>
        """
        
        tables = _parse_table_with_bs4(html)
        assert len(tables) == 1
        
        df = tables[0]
        assert len(df) == 2
        assert list(df.columns) == ["Symbol", "LTP", "Volume"]
        assert df.iloc[0]["Symbol"] == "NABIL"
        assert df.iloc[1]["LTP"] == "800.00"
    
    def test_parse_malformed_table_no_thead(self):
        """Test parsing table without thead (headers in tbody)."""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>Symbol</td>
                    <td>LTP</td>
                    <td>Volume</td>
                </tr>
                <tr>
                    <td>NABIL</td>
                    <td>1,200.00</td>
                    <td>10,000</td>
                </tr>
            </tbody>
        </table>
        """
        
        tables = _parse_table_with_bs4(html)
        assert len(tables) == 1
        
        df = tables[0]
        assert len(df) == 1  # Header row removed
        assert list(df.columns) == ["Symbol", "LTP", "Volume"]
        assert df.iloc[0]["Symbol"] == "NABIL"
    
    def test_parse_table_with_nested_elements(self):
        """Test parsing table with nested HTML elements (like ShareSansar)."""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>Symbol</td>
                    <td>LTP</td>
                    <td>Change</td>
                </tr>
                <tr>
                    <td><a href="/company/NABIL">NABIL</a></td>
                    <td><span class="price">1,200.00</span></td>
                    <td><span class="positive">+10.50</span></td>
                </tr>
                <tr>
                    <td><div>HBL</div></td>
                    <td>800.00</td>
                    <td><span class="negative">-5.20</span></td>
                </tr>
            </tbody>
        </table>
        """
        
        tables = _parse_table_with_bs4(html)
        assert len(tables) == 1
        
        df = tables[0]
        assert len(df) == 2
        assert df.iloc[0]["Symbol"] == "NABIL"
        assert df.iloc[0]["LTP"] == "1,200.00"
        assert df.iloc[0]["Change"] == "+10.50"
    
    def test_parse_table_with_extra_whitespace(self):
        """Test parsing table with extra whitespace and newlines."""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>
                        Symbol
                    </td>
                    <td>LTP</td>
                </tr>
                <tr>
                    <td>
                        NABIL
                    </td>
                    <td>
                        1,200.00
                    </td>
                </tr>
            </tbody>
        </table>
        """
        
        tables = _parse_table_with_bs4(html)
        assert len(tables) == 1
        
        df = tables[0]
        assert len(df) == 1
        assert df.iloc[0]["Symbol"] == "NABIL"
        assert df.iloc[0]["LTP"] == "1,200.00"
    
    def test_parse_multiple_tables(self):
        """Test parsing HTML with multiple tables."""
        html = """
        <div>
            <table id="summary">
                <tbody>
                    <tr><td>Total Volume</td><td>1,000,000</td></tr>
                </tbody>
            </table>
            
            <table id="stocks">
                <thead>
                    <tr><th>Symbol</th><th>LTP</th></tr>
                </thead>
                <tbody>
                    <tr><td>NABIL</td><td>1200</td></tr>
                    <tr><td>HBL</td><td>800</td></tr>
                </tbody>
            </table>
        </div>
        """
        
        tables = _parse_table_with_bs4(html)
        # The first table might not have proper headers, so only the second table is parsed
        assert len(tables) >= 1
        
        # Find the stocks table
        stocks_table = None
        for table in tables:
            if "Symbol" in table.columns and len(table) == 2:
                stocks_table = table
                break
        
        assert stocks_table is not None
        assert len(stocks_table) == 2
        assert "NABIL" in stocks_table["Symbol"].values
    
    def test_choose_market_table_scoring(self):
        """Test table selection scoring for market data."""
        # Good market data table
        market_table = pd.DataFrame({
            "Symbol": ["NABIL", "HBL"],
            "LTP": [1200, 800],
            "Volume": [10000, 5000],
            "Turnover": [1200000, 400000]
        })
        
        # Bad table (no market data)
        bad_table = pd.DataFrame({
            "Name": ["John", "Jane"],
            "Age": [30, 25]
        })
        
        tables = [bad_table, market_table]
        selected = _choose_market_table(tables)
        
        assert len(selected) == 2
        assert "Symbol" in selected.columns
        assert "LTP" in selected.columns
    
    def test_choose_market_table_fallback(self):
        """Test fallback when no ideal table is found."""
        # Table with some market data but missing key columns
        partial_table = pd.DataFrame({
            "Code": ["NABIL", "HBL"],
            "Price": [1200, 800]
        })
        
        tables = [partial_table]
        selected = _choose_market_table(tables)
        
        assert len(selected) == 2
        assert "Code" in selected.columns
    
    def test_empty_table_handling(self):
        """Test handling of empty or malformed tables."""
        html = """
        <table>
            <tbody>
                <tr></tr>
                <tr><td></td><td></td></tr>
            </tbody>
        </table>
        """
        
        tables = _parse_table_with_bs4(html)
        # Should handle gracefully, might return empty table or skip
        assert isinstance(tables, list)

    def test_parse_browser_repaired_missing_closing_tags(self):
        """Test parsing rows from HTML that relies on browser repair."""
        html = """
        <div class="col-md-12">
          <table>
            <tbody>
              <tr><td>Symbol<td>LTP<td>Volume
              <tr><td><a href="/company/NABIL">NABIL</a><td><span>1,200.00</span><td>10,000
              <tr><td>HBL<td>800.00<td>5,000
            </tbody>
          </table>
        """

        tables = _parse_table_with_bs4(html)

        assert len(tables) == 1
        df = tables[0]
        assert list(df.columns) == ["Symbol", "LTP", "Volume"]
        assert len(df) == 2
        assert df.iloc[0]["Symbol"] == "NABIL"
        assert df.iloc[1]["Volume"] == "5,000"

    def test_nested_table_rows_do_not_leak_into_parent_table(self):
        """Test direct-row parsing ignores unrelated nested table rows."""
        html = """
        <table id="stocks">
          <thead><tr><th>Symbol</th><th>LTP</th></tr></thead>
          <tbody>
            <tr>
              <td>NABIL</td>
              <td>
                1,200.00
                <table><tbody><tr><td>Nested label</td><td>Nested value</td></tr></tbody></table>
              </td>
            </tr>
            <tr><td>HBL</td><td>800.00</td></tr>
          </tbody>
        </table>
        """

        tables = _parse_table_with_bs4(html)

        assert len(tables) >= 1
        df = tables[0]
        assert len(df) == 2
        assert df.iloc[0]["Symbol"] == "NABIL"
        assert "Nested label" not in df["Symbol"].values

    def test_duplicate_and_blank_headers_are_stable(self):
        """Test duplicate and blank headers get safe DataFrame names."""
        html = """
        <table>
          <thead><tr><th>Symbol</th><th></th><th>Symbol</th></tr></thead>
          <tbody><tr><td>NABIL</td><td>1,200</td><td>NABIL</td></tr></tbody>
        </table>
        """

        tables = _parse_table_with_bs4(html)

        assert len(tables) == 1
        assert list(tables[0].columns) == ["Symbol", "col_2", "Symbol_2"]

    def test_large_sharesansar_shaped_table(self):
        """Test a 346-row by 24-column stock table parses without fallback."""
        headers = ["Symbol", "LTP", "Volume", "Turnover"] + [f"Metric {i}" for i in range(5, 25)]
        header_html = "".join(f"<td>{header}</td>" for header in headers)
        rows = []
        for index in range(346):
            cells = [
                f"<td><a href='/company/SYM{index}'>SYM{index}</a></td>",
                f"<td><span class='price'>{100 + index}</span></td>",
                f"<td>{1000 + index}</td>",
                f"<td>{100000 + index}</td>",
            ]
            cells.extend(f"<td>{index}-{col}</td>" for col in range(5, 25))
            rows.append(f"<tr class='success-index'>{''.join(cells)}</tr>")

        html = f"<table><tbody><tr>{header_html}</tr>{''.join(rows)}</tbody></table>"

        tables = _parse_table_with_bs4(html)
        selected = _choose_market_table(tables)

        assert len(selected) == 346
        assert len(selected.columns) == 24
        assert selected.iloc[345]["Symbol"] == "SYM345"
