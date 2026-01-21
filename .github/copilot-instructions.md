# Copilot Instructions for congenial-octo-telegram

## Project Overview

Python learning project with two production features:
1. **Email reporting automation** (`reporting/email_report.py`) - Multi-account IMAP/POP3 email aggregation with Excel report generation
2. **Maltego transforms** (`maltego/maltego-trx/maltego_trx.py`) - File system enumeration transform with configurable recursion

## Architecture & Data Flow

### Email Reporting System

**Entry point**: `reporting/email_report.py` (452 lines)

**Data flow**:
1. `discover_accounts()` → scans environment for `ACCOUNT_N_EMAIL` patterns (supports unlimited accounts)
2. `fetch_from_account()` → dispatches to IMAP/POP3 handlers per account
3. `fetch_from_imap()` / `fetch_from_pop3()` → returns list of email dicts (from, to, subject, date, account)
4. Main aggregates into `master_list`, converts to `pandas.DataFrame`
5. `send_consolidated_report()` → generates `.xlsx` with `xlsxwriter`, emails via SMTP

**Multi-provider support**: Each account independently configures protocol (IMAP/POP3) and server. Sender account can use different SMTP provider.

**Configuration pattern**: Environment variables with numbered accounts:
```powershell
$env:ACCOUNT_1_EMAIL="support@gmail.com"
$env:ACCOUNT_1_PASS="app-password"
$env:ACCOUNT_1_PROTOCOL="IMAP"  # Optional, defaults to IMAP
$env:ACCOUNT_1_SERVER="imap.gmail.com"  # Optional, server auto-detected
```

See [RUNNING_EMAIL_REPORT.md](../RUNNING_EMAIL_REPORT.md) for full launch instructions including Gmail app password setup.

### Maltego Transform System

**Transform**: `maltego/maltego-trx/maltego_trx.py` - `ListFiles` class
- Uses `os.scandir()` for efficiency (not `os.walk()`)
- Returns `maltego.File` entities with properties: `path`, `depth`, `parent`, `relative_path`, `filesize`
- Recursion controlled via environment: `LISTFILES_RECURSIVE=1` (default), `LISTFILES_MAXDEPTH=N`
- Partial error handling: continues on permission errors using `response.addUIMessage(..., messageType='PartialError')`

**Why standalone**: Transform is a script, not an installed package, hence dynamic loading pattern in tests.

## Critical Testing Patterns

### Manual Mocking (NOT unittest.mock)

Tests (`tests/test_listfiles.py`, `scripts/run_listfiles_test.py`) use explicit mock classes:
```python
class MockRequest:
    def __init__(self, value, props=None):
        self.Value = value
        self.Properties = props or {}

class MockResponse:
    def __init__(self):
        self.entities = []
        self.messages = []
```

**Reason**: Provides transparency for simulating Maltego API without framework dependency.

### Dynamic Module Loading

Pattern used universally for loading `maltego_trx.py`:
```python
spec = importlib.util.spec_from_file_location("maltego_trx", abs_path)
module = importlib.util.module_from_spec(spec)
# Mock dependencies before loading
sys.modules['maltego_trx'] = types.ModuleType('maltego_trx')
sys.modules['maltego_trx.transform'] = transform_mod  # with DiscoverableTransform
spec.loader.exec_module(module)
```

### Test Commands

```powershell
# All tests (from project root)
python -m pytest -q

# Specific suites
python -m pytest tests/test_email_report.py -v
python -m pytest tests/test_listfiles.py -v

# Coverage report
pip install pytest-cov
python -m pytest tests/ --cov=reporting --cov-report=html

# Manual transform test (outputs JSON)
python scripts/run_listfiles_test.py
```

See [tests/README_TESTS.md](../tests/README_TESTS.md) for detailed test documentation.

### Continuous Integration

**GitHub Actions**: Automated testing on push/PR via `.github/workflows/tests.yml`
- Runs on Ubuntu and Windows
- Tests Python 3.8, 3.9, 3.10, 3.11, 3.12
- Generates coverage reports (Python 3.11 on Ubuntu)
- Workflow can be triggered manually from Actions tab

**Local CI simulation**:
```powershell
# Run tests exactly as CI does
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest tests/ -v --tb=short
```

## Developer Workflows

### Running Email Report

1. Activate virtual environment: `.\.venv\Scripts\Activate.ps1`
2. Set environment variables (see `.env.example` or [RUNNING_EMAIL_REPORT.md](../RUNNING_EMAIL_REPORT.md))
3. Run: `python reporting/email_report.py`
4. Output: `consolidated_email_report.xlsx` + logs to `email_report.log`

**Gmail requirement**: Must use app passwords, not regular passwords ([setup instructions](https://myaccount.google.com/apppasswords))

### Adding Transform Properties

In `maltego_trx.py` within `iter_files()` loop:
```python
ent.addProperty("property_name", "Display Name", "strict"|"loose", value)
```
- `"strict"`: precise values (paths, integers, preserves type semantics)
- `"loose"`: display-only (formatted strings like file sizes)

Update `tests/test_listfiles.py` to validate new properties.

### Creating New Transform Classes

Follow the `ListFiles` pattern in `maltego/maltego-trx/maltego_trx.py`:

```python
from maltego_trx.transform import DiscoverableTransform

class MyNewTransform(DiscoverableTransform):
    """Brief description of what this transform does."""
    
    @classmethod
    def create_entities(cls, request, response):
        # 1. Extract input from request
        input_value = request.Value
        
        # 2. Validate input
        if not is_valid(input_value):
            response.addUIMessage("Error message", messageType='PartialError')
            return
        
        # 3. Read configuration (environment + request properties)
        env_config = os.environ.get('MY_CONFIG', 'default')
        req_config = cls._get_req_param(request, 'config_name')
        
        # 4. Process and create entities
        for item in process_items(input_value):
            try:
                ent = response.addEntity("maltego.EntityType", item.value)
                ent.addProperty("prop1", "Display Name", "strict", item.prop1)
                # Add more properties...
            except Exception as e:
                response.addUIMessage(f"Failed: {e}", messageType='PartialError')
        
        # 5. Add summary message
        response.addUIMessage(f"Processed {count} items")
```

**Key patterns:**
- Inherit from `DiscoverableTransform`
- Use `@classmethod` with `create_entities(cls, request, response)`
- Use `PartialError` for recoverable errors (transform continues)
- Extract config from environment (`os.environ.get()`) or request properties
- Add entities with `response.addEntity(type, value)` then set properties
- Always add summary message at end

**Testing new transforms:**
1. Add mock test in `tests/test_*.py` following `test_listfiles.py` pattern
2. Create manual harness in `scripts/run_*_test.py` for JSON output
3. Mock `maltego_trx.transform.DiscoverableTransform` before loading module

## Security Best Practices

### Credential Management

- **Never commit credentials**: `.env` is in `.gitignore` - always use `.env.example` as template
- **Use app passwords**: Gmail/Yahoo require app-specific passwords, not account passwords
- **Rotate credentials**: Periodically regenerate app passwords, especially for bot accounts
- **Separate bot accounts**: Use dedicated email accounts for automation (not personal accounts)
- **Minimal permissions**: Bot accounts should only have access to necessary mailboxes

### Code Safety

- **Validate before logging**: Email reporter logs extensively - ensure no passwords in log messages
- **Environment variable isolation**: Test accounts use numbered pattern (`ACCOUNT_N_*`) to avoid variable collisions
- **Default to secure**: IMAP uses SSL by default (`IMAP4_SSL`), POP3 uses `POP3_SSL`
- **Timeout protection**: All network operations have configurable timeouts (`IMAP_TIMEOUT`, default 60s)

### Testing with Real Credentials

If testing with real accounts:
```powershell
# Set minimal test account (read-only operations)
$env:ACCOUNT_1_EMAIL="test-readonly@gmail.com"
$env:ACCOUNT_1_PASS="temp-app-password"
$env:DAYS_BACK="1"  # Limit scope

# Clear after testing
Remove-Item Env:ACCOUNT_1_EMAIL, Env:ACCOUNT_1_PASS
```

**Never** commit test credentials or include them in error reports/issues.

## Project-Specific Conventions

### Relative Path Resolution

All scripts calculate paths relative to their location (avoids hard-coded drives):
```python
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
```

### Logging Pattern (Email Reporter)

Uses Python `logging` module with dual handlers (file + console):
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_report.log'),
        logging.StreamHandler()
    ]
)
```

### Error Handling Philosophy

- **Transforms**: Use partial errors to continue processing (`addUIMessage(..., messageType='PartialError')`)
- **Email reporter**: Retry logic with exponential backoff (3 retries), logs warnings but continues with other accounts

## File Structure Notes

- `.env.example` → template for email credentials (never commit `.env`)
- `RUNNING_EMAIL_REPORT.md` → comprehensive setup guide (538 lines) with provider-specific instructions
- `TEST_SUITE_SUMMARY.md` → test coverage overview
- `.github/agents/README.md` → unrelated task manager app (ignore for this project)
