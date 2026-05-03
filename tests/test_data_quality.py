from api.services.csv_service import data_quality


def test_data_quality_report_is_generated():
    report = data_quality()["data"]

    assert report["rows_checked"] > 250000
    assert report["duplicate_symbol_date_rows"] == 0
    assert report["future_date_rows"] == 0
    assert report["status"] in {"passing", "warning"}
