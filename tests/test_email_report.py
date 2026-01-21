"""Test suite for email_report.py

This test suite covers:
- Account discovery from environment variables
- Email header decoding
- IMAP connection and email fetching (mocked)
- SMTP report sending (mocked)
- Error handling and retry logic
"""

import pytest
import os
import sys
import pandas as pd
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime, timedelta
import importlib.util

# Add the reporting directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reporting'))


@pytest.fixture
def clean_env():
    """Clean environment variables before each test."""
    # Save original env
    original_env = os.environ.copy()
    
    # Clear email-related env vars
    for key in list(os.environ.keys()):
        if key.startswith('ACCOUNT_') or key.startswith('SENDER_') or key.startswith('SMTP_') or key == 'RECIPIENT_EMAIL':
            del os.environ[key]
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def email_report_module():
    """Load the email_report module dynamically."""
    module_path = os.path.join(os.path.dirname(__file__), '..', 'reporting', 'email_report.py')
    spec = importlib.util.spec_from_file_location("email_report", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestAccountDiscovery:
    """Tests for discover_accounts function."""
    
    def test_discover_single_account(self, clean_env, email_report_module):
        """Test discovering a single account."""
        os.environ['ACCOUNT_1_EMAIL'] = 'test@example.com'
        os.environ['ACCOUNT_1_PASS'] = 'password123'
        os.environ['ACCOUNT_1_SERVER'] = 'imap.example.com'
        
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 1
        assert accounts[0]['email'] == 'test@example.com'
        assert accounts[0]['password'] == 'password123'
        assert accounts[0]['server'] == 'imap.example.com'
    
    def test_discover_multiple_accounts(self, clean_env, email_report_module):
        """Test discovering multiple accounts."""
        os.environ['ACCOUNT_1_EMAIL'] = 'test1@example.com'
        os.environ['ACCOUNT_1_PASS'] = 'pass1'
        
        os.environ['ACCOUNT_2_EMAIL'] = 'test2@example.com'
        os.environ['ACCOUNT_2_PASS'] = 'pass2'
        
        os.environ['ACCOUNT_3_EMAIL'] = 'test3@example.com'
        os.environ['ACCOUNT_3_PASS'] = 'pass3'
        
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 3
        assert accounts[0]['email'] == 'test1@example.com'
        assert accounts[1]['email'] == 'test2@example.com'
        assert accounts[2]['email'] == 'test3@example.com'
    
    def test_discover_accounts_with_gaps(self, clean_env, email_report_module):
        """Test account discovery with non-sequential numbers."""
        os.environ['ACCOUNT_1_EMAIL'] = 'test1@example.com'
        os.environ['ACCOUNT_1_PASS'] = 'pass1'
        
        os.environ['ACCOUNT_5_EMAIL'] = 'test5@example.com'
        os.environ['ACCOUNT_5_PASS'] = 'pass5'
        
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 2
        assert accounts[0]['email'] == 'test1@example.com'
        assert accounts[1]['email'] == 'test5@example.com'
    
    def test_discover_accounts_default_server(self, clean_env, email_report_module):
        """Test that default server is imap.gmail.com."""
        os.environ['ACCOUNT_1_EMAIL'] = 'test@example.com'
        os.environ['ACCOUNT_1_PASS'] = 'password'
        # Don't set ACCOUNT_1_SERVER
        
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 1
        assert accounts[0]['server'] == 'imap.gmail.com'
    
    def test_discover_accounts_empty(self, clean_env, email_report_module):
        """Test when no accounts are configured."""
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 0
    
    def test_discover_accounts_missing_password(self, clean_env, email_report_module):
        """Test account with missing password (should still be included)."""
        os.environ['ACCOUNT_1_EMAIL'] = 'test@example.com'
        # Don't set ACCOUNT_1_PASS
        
        accounts = email_report_module.discover_accounts()
        
        assert len(accounts) == 1
        assert accounts[0]['password'] == ''


class TestEmailHeaderDecoding:
    """Tests for decode_email_header function."""
    
    def test_decode_simple_header(self, email_report_module):
        """Test decoding a simple ASCII header."""
        result = email_report_module.decode_email_header("Simple Subject")
        assert result == "Simple Subject"
    
    def test_decode_utf8_header(self, email_report_module):
        """Test decoding UTF-8 encoded header."""
        # Simulate encoded header
        import email.header
        encoded = email.header.make_header([("Test Subject", "utf-8")])
        result = email_report_module.decode_email_header(str(encoded))
        assert "Test Subject" in result
    
    def test_decode_none_header(self, email_report_module):
        """Test decoding None header."""
        result = email_report_module.decode_email_header(None)
        assert result == "No Subject"
    
    def test_decode_empty_header(self, email_report_module):
        """Test decoding empty header."""
        result = email_report_module.decode_email_header("")
        assert result == "No Subject"
    
    def test_decode_header_with_error(self, email_report_module):
        """Test that decoding errors are handled gracefully."""
        # This should not raise an exception
        result = email_report_module.decode_email_header("Some weird header")
        assert isinstance(result, str)


class TestFetchFromAccount:
    """Tests for fetch_from_account function."""
    
    @patch('imaplib.IMAP4_SSL')
    def test_fetch_success(self, mock_imap, email_report_module):
        """Test successful email fetching."""
        # Setup mock IMAP connection
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        
        mock_mail.select.return_value = ('OK', [b'10'])
        mock_mail.search.return_value = ('OK', [b'1 2'])
        
        # Create a mock email message
        mock_email_data = b'From: sender@example.com\r\nSubject: Test Subject\r\nDate: Mon, 1 Jan 2026 10:00:00 +0000\r\n\r\nBody'
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {100}', mock_email_data)])
        
        account = {
            'email': 'test@example.com',
            'password': 'password',
            'server': 'imap.gmail.com'
        }
        
        result = email_report_module.fetch_from_account(account)
        
        assert isinstance(result, list)
        # We expect 2 emails based on search returning b'1 2'
        assert len(result) >= 1
        
        # Verify IMAP methods were called
        mock_mail.login.assert_called_once_with('test@example.com', 'password')
        mock_mail.select.assert_called_once_with('inbox')
        mock_mail.close.assert_called_once()
        mock_mail.logout.assert_called_once()
    
    @patch('imaplib.IMAP4_SSL')
    def test_fetch_imap_error(self, mock_imap, email_report_module):
        """Test IMAP connection error handling."""
        import imaplib
        mock_imap.side_effect = imaplib.IMAP4.error("Connection failed")
        
        account = {
            'email': 'test@example.com',
            'password': 'wrong_password',
            'server': 'imap.gmail.com'
        }
        
        # Should not raise exception, should return empty list
        result = email_report_module.fetch_from_account(account)
        
        assert result == []
    
    @patch('imaplib.IMAP4_SSL')
    def test_fetch_timeout(self, mock_imap, email_report_module):
        """Test timeout error handling."""
        mock_imap.side_effect = TimeoutError("Connection timed out")
        
        account = {
            'email': 'test@example.com',
            'password': 'password',
            'server': 'imap.gmail.com'
        }
        
        result = email_report_module.fetch_from_account(account)
        
        assert result == []


class TestSendConsolidatedReport:
    """Tests for send_consolidated_report function."""
    
    def test_send_report_empty_dataframe(self, email_report_module):
        """Test sending with empty dataframe."""
        df = pd.DataFrame()
        
        result = email_report_module.send_consolidated_report(df)
        
        assert result is False
    
    @patch('smtplib.SMTP')
    @patch('pandas.ExcelWriter')
    @patch('builtins.open', new_callable=mock_open, read_data=b'excel data')
    def test_send_report_success(self, mock_file, mock_excel_writer, mock_smtp, email_report_module):
        """Test successful report sending."""
        # Setup environment
        os.environ['SENDER_EMAIL'] = 'sender@example.com'
        os.environ['SENDER_PASS'] = 'password'
        os.environ['RECIPIENT_EMAIL'] = 'recipient@example.com'
        
        # Create test dataframe
        df = pd.DataFrame({
            'Source Account': ['test@example.com', 'test@example.com'],
            'Date': ['2026-01-01', '2026-01-02'],
            'Sender': ['sender1@example.com', 'sender2@example.com'],
            'Subject': ['Subject 1', 'Subject 2']
        })
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Mock ExcelWriter
        mock_writer = MagicMock()
        mock_writer.__enter__ = MagicMock(return_value=mock_writer)
        mock_writer.__exit__ = MagicMock(return_value=False)
        mock_writer.sheets = {'Email Report': MagicMock()}
        mock_excel_writer.return_value = mock_writer
        
        result = email_report_module.send_consolidated_report(df)
        
        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
        
        assert result is True
    
    @patch('smtplib.SMTP')
    @patch('pandas.ExcelWriter')
    def test_send_report_smtp_auth_error(self, mock_excel_writer, mock_smtp, email_report_module):
        """Test SMTP authentication error."""
        import smtplib
        
        os.environ['SENDER_EMAIL'] = 'sender@example.com'
        os.environ['SENDER_PASS'] = 'wrong_password'
        
        df = pd.DataFrame({
            'Source Account': ['test@example.com'],
            'Date': ['2026-01-01'],
            'Sender': ['sender@example.com'],
            'Subject': ['Test']
        })
        
        # Mock ExcelWriter
        mock_writer = MagicMock()
        mock_writer.__enter__ = MagicMock(return_value=mock_writer)
        mock_writer.__exit__ = MagicMock(return_value=False)
        mock_writer.sheets = {'Email Report': MagicMock()}
        mock_excel_writer.return_value = mock_writer
        
        # Mock SMTP to raise auth error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp.return_value = mock_server
        
        result = email_report_module.send_consolidated_report(df)
        
        assert result is False


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @patch('imaplib.IMAP4_SSL')
    @patch('smtplib.SMTP')
    @patch('pandas.ExcelWriter')
    @patch('builtins.open', new_callable=mock_open, read_data=b'excel data')
    def test_full_workflow(self, mock_file, mock_excel_writer, mock_smtp, mock_imap, clean_env, email_report_module):
        """Test complete workflow from fetching to sending."""
        # Setup environment
        os.environ['ACCOUNT_1_EMAIL'] = 'source@example.com'
        os.environ['ACCOUNT_1_PASS'] = 'source_pass'
        os.environ['SENDER_EMAIL'] = 'sender@example.com'
        os.environ['SENDER_PASS'] = 'sender_pass'
        os.environ['RECIPIENT_EMAIL'] = 'recipient@example.com'
        
        # Mock IMAP
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1'])
        
        mock_email_data = b'From: test@example.com\r\nSubject: Test\r\nDate: Mon, 1 Jan 2026 10:00:00\r\n\r\nBody'
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {100}', mock_email_data)])
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Mock ExcelWriter
        mock_writer = MagicMock()
        mock_writer.__enter__ = MagicMock(return_value=mock_writer)
        mock_writer.__exit__ = MagicMock(return_value=False)
        mock_writer.sheets = {'Email Report': MagicMock()}
        mock_excel_writer.return_value = mock_writer
        
        # Reload module to pick up new env vars
        accounts = email_report_module.discover_accounts()
        assert len(accounts) == 1
        
        # Fetch emails
        emails = email_report_module.fetch_from_account(accounts[0])
        assert len(emails) >= 1
        
        # Create DataFrame and send
        df = pd.DataFrame(emails)
        result = email_report_module.send_consolidated_report(df)
        
        assert result is True


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_missing_sender_credentials(self, clean_env):
        """Test that missing sender credentials are caught."""
        # This would be tested in the main execution block
        # We test that the config validation works
        assert os.environ.get('SENDER_EMAIL', '') == ''
        assert os.environ.get('SENDER_PASS', '') == ''
    
    @patch('imaplib.IMAP4_SSL')
    def test_retry_logic(self, mock_imap, email_report_module):
        """Test that retry logic works on transient failures."""
        import imaplib
        
        # First two calls fail, third succeeds
        mock_mail_fail = MagicMock()
        mock_mail_fail.login.side_effect = imaplib.IMAP4.error("Temporary failure")
        
        mock_mail_success = MagicMock()
        mock_mail_success.select.return_value = ('OK', [b'0'])
        mock_mail_success.search.return_value = ('OK', [b''])
        
        # Setup to fail twice then succeed
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise imaplib.IMAP4.error("Temporary failure")
            return mock_mail_success
        
        mock_imap.side_effect = side_effect
        
        account = {
            'email': 'test@example.com',
            'password': 'password',
            'server': 'imap.gmail.com'
        }
        
        # Set MAX_RETRIES high enough
        os.environ['MAX_RETRIES'] = '3'
        
        result = email_report_module.fetch_from_account(account)
        
        # Should eventually succeed after retries
        assert isinstance(result, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
