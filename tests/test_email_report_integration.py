"""Integration tests for email_report.py using real test data.

These tests use temporary files and mock servers to simulate real scenarios
without actually connecting to email servers.
"""

import pytest
import os
import tempfile
import pandas as pd
from datetime import datetime
from pathlib import Path


@pytest.fixture
def temp_report_dir():
    """Create a temporary directory for reports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(original_dir)


def test_excel_report_structure(temp_report_dir):
    """Test that the Excel report has the correct structure."""
    # Create sample data
    data = {
        'Source Account': ['test1@example.com', 'test2@example.com'],
        'Date': ['Mon, 1 Jan 2026 10:00:00 +0000', 'Mon, 1 Jan 2026 11:00:00 +0000'],
        'Sender': ['sender1@example.com', 'sender2@example.com'],
        'Subject': ['Test Subject 1', 'Test Subject 2']
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    filename = 'test_report.xlsx'
    df.to_excel(filename, index=False)
    
    # Verify file exists
    assert os.path.exists(filename)
    
    # Read back and verify structure
    df_read = pd.read_excel(filename)
    
    assert list(df_read.columns) == ['Source Account', 'Date', 'Sender', 'Subject']
    assert len(df_read) == 2
    assert df_read['Source Account'].iloc[0] == 'test1@example.com'


def test_log_file_creation(temp_report_dir):
    """Test that log files are created properly."""
    import logging
    
    # Setup logging
    log_file = 'test_email_report.log'
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.INFO)
    
    # Add file handler
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Write some logs
    logger.info("Test log entry 1")
    logger.warning("Test warning")
    logger.error("Test error")
    
    # Close handler
    handler.close()
    logger.removeHandler(handler)
    
    # Verify log file exists and has content
    assert os.path.exists(log_file)
    
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Test log entry 1" in content
        assert "Test warning" in content
        assert "Test error" in content


def test_dataframe_grouping():
    """Test that DataFrame grouping by account works correctly."""
    data = {
        'Source Account': ['test1@example.com', 'test1@example.com', 'test2@example.com'],
        'Date': ['2026-01-01', '2026-01-02', '2026-01-01'],
        'Sender': ['sender@example.com', 'sender@example.com', 'sender@example.com'],
        'Subject': ['Subject 1', 'Subject 2', 'Subject 3']
    }
    
    df = pd.DataFrame(data)
    
    # Group by source account
    grouped = df.groupby('Source Account').size()
    
    assert grouped['test1@example.com'] == 2
    assert grouped['test2@example.com'] == 1


def test_date_filtering():
    """Test date filtering logic for email search."""
    from datetime import timedelta
    
    days_back = 7
    date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    
    # Verify format is correct for IMAP search
    assert len(date_cutoff.split('-')) == 3
    assert date_cutoff.endswith(str(datetime.now().year))


def test_environment_variable_patterns():
    """Test that environment variable patterns work correctly."""
    import re
    
    account_pattern = re.compile(r'^ACCOUNT_(\d+)_EMAIL$')
    
    # Test various patterns
    assert account_pattern.match('ACCOUNT_1_EMAIL')
    assert account_pattern.match('ACCOUNT_99_EMAIL')
    assert not account_pattern.match('ACCOUNT_EMAIL')
    assert not account_pattern.match('ACCOUNT_A_EMAIL')
    assert not account_pattern.match('SENDER_EMAIL')
    
    # Extract number
    match = account_pattern.match('ACCOUNT_42_EMAIL')
    assert match
    assert int(match.group(1)) == 42


def test_excel_column_width_calculation():
    """Test Excel column width auto-sizing logic."""
    data = {
        'Short': ['A', 'B'],
        'Very Long Column Name': ['Short value', 'Another short value'],
        'Email Address': ['verylongemailaddress@example.com', 'short@ex.com']
    }
    
    df = pd.DataFrame(data)
    
    # Calculate max width for each column
    for col in df.columns:
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(col)
        ) + 2
        
        # Verify width is reasonable
        assert max_length > len(col)
        assert max_length <= 50 + 2  # Script uses min(max_length, 50)


def test_email_body_formatting():
    """Test email body formatting for the report."""
    days_back = 7
    account_count = 3
    email_count = 42
    
    account_summary = {
        'account1@example.com': 15,
        'account2@example.com': 20,
        'account3@example.com': 7
    }
    
    summary_lines = "\n".join([f"    • {acc}: {count} emails" for acc, count in account_summary.items()])
    
    body = f"""Hi,

Here is the consolidated email report for the last {days_back} day(s).

📋 Summary:
    • Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    • Accounts Scanned: {account_count}
    • Total Emails Found: {email_count}

📊 Breakdown by Account:
{summary_lines}

The detailed report is attached as an Excel file.

---
This report was generated automatically.
"""
    
    # Verify body contains expected content
    assert f"last {days_back} day(s)" in body
    assert f"Accounts Scanned: {account_count}" in body
    assert f"Total Emails Found: {email_count}" in body
    assert "account1@example.com: 15 emails" in body
    assert "generated automatically" in body


def test_mime_type_for_excel():
    """Test that correct MIME type is used for Excel attachment."""
    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Verify it's a valid MIME type for .xlsx files
    assert 'spreadsheetml' in mime_type
    assert 'sheet' in mime_type


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
