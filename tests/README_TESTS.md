# Email Report Test Suite

## Overview

This test suite provides comprehensive coverage for the email reporting functionality.

## Test Files

### `test_email_report.py`
Main unit tests covering:
- **Account Discovery**: Testing dynamic environment variable scanning
- **Email Header Decoding**: UTF-8, ASCII, and error handling
- **IMAP Fetching**: Mocked connection, error handling, retry logic
- **SMTP Sending**: Mocked email sending, authentication errors
- **Integration**: Full workflow from fetch to send
- **Error Handling**: Validation, timeouts, retries

### `test_email_report_integration.py`
Integration tests covering:
- Excel report structure and formatting
- Log file creation and content
- DataFrame operations and grouping
- Date filtering logic
- Environment variable pattern matching
- Email body formatting
- MIME type handling

### `test_listfiles.py`
Tests for the Maltego file listing transform:
- Non-recursive file listing
- Recursive file listing with subdirectories

## Running Tests

### Run All Tests

```powershell
# From project root
python -m pytest tests/ -v
```

### Run Specific Test File

```powershell
# Email report tests only
python -m pytest tests/test_email_report.py -v

# Integration tests only
python -m pytest tests/test_email_report_integration.py -v

# Maltego tests only
python -m pytest tests/test_listfiles.py -v
```

### Run Specific Test Class or Function

```powershell
# Run only account discovery tests
python -m pytest tests/test_email_report.py::TestAccountDiscovery -v

# Run a specific test function
python -m pytest tests/test_email_report.py::TestAccountDiscovery::test_discover_single_account -v
```

### Run with Coverage Report

```powershell
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
python -m pytest tests/ --cov=reporting --cov-report=html

# View coverage report
start htmlcov/index.html  # Opens in browser
```

### Run with Verbose Output

```powershell
# Show all test names and results
python -m pytest tests/ -v

# Show print statements
python -m pytest tests/ -v -s

# Show detailed failure information
python -m pytest tests/ -v --tb=long
```

## Test Coverage

### Unit Tests (test_email_report.py)

| Component | Coverage |
|-----------|----------|
| `discover_accounts()` | ✅ Multiple scenarios |
| `decode_email_header()` | ✅ UTF-8, ASCII, None, errors |
| `fetch_from_account()` | ✅ Success, IMAP errors, timeouts |
| `send_consolidated_report()` | ✅ Success, empty data, SMTP errors |
| Retry logic | ✅ Exponential backoff |
| Error handling | ✅ All exception types |

### Integration Tests (test_email_report_integration.py)

| Feature | Coverage |
|---------|----------|
| Excel report creation | ✅ |
| Log file generation | ✅ |
| DataFrame operations | ✅ |
| Date formatting | ✅ |
| Email body formatting | ✅ |
| Environment variable patterns | ✅ |

## Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Tests for new feature."""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return {'key': 'value'}
    
    def test_feature_success(self, setup_data):
        """Test successful operation."""
        # Arrange
        input_data = setup_data
        
        # Act
        result = some_function(input_data)
        
        # Assert
        assert result == expected_value
    
    def test_feature_error(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            some_function(invalid_input)
```

### Using Mocks

```python
@patch('imaplib.IMAP4_SSL')
def test_with_mock_imap(mock_imap):
    """Test with mocked IMAP connection."""
    # Setup mock
    mock_mail = Mock()
    mock_imap.return_value = mock_mail
    mock_mail.login.return_value = ('OK', [b'Logged in'])
    
    # Run test
    result = fetch_from_account(account)
    
    # Verify mock was called
    mock_mail.login.assert_called_once()
```

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=reporting
```

## Troubleshooting

### Tests Fail to Import Module

**Problem:** `ModuleNotFoundError: No module named 'reporting'`

**Solution:** Run tests from project root:
```powershell
cd C:\workspace\congenial-octo-telegram
python -m pytest tests/ -v
```

### Mock Not Working

**Problem:** Real connections are being made instead of using mocks

**Solution:** Ensure patches are applied before module import:
```python
@patch('imaplib.IMAP4_SSL')
def test_function(mock_imap):
    # Test code here
```

### Environment Variables Persist

**Problem:** Tests fail due to env vars from previous tests

**Solution:** Use the `clean_env` fixture:
```python
def test_with_clean_env(clean_env):
    # Environment is cleaned before this test
```

### Async/Timeout Issues

**Problem:** Tests hang or timeout

**Solution:** Add timeout markers:
```python
@pytest.mark.timeout(5)  # 5 second timeout
def test_long_running():
    pass
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear, descriptive test names
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mock External Services**: Don't make real IMAP/SMTP connections
5. **Test Edge Cases**: Test empty inputs, None values, errors
6. **Fast Tests**: Keep unit tests under 1 second each
7. **Clean Up**: Use fixtures to clean up environment/files

## Getting Help

- Check test output for detailed error messages
- Use `-v` flag for verbose output
- Use `-s` flag to see print statements
- Check `pytest` documentation: https://docs.pytest.org/
