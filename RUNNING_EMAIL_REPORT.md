# Email Report Script - Launch Instructions

## Overview

This script connects to multiple email accounts, fetches recent emails, and generates a consolidated Excel report that is automatically emailed to a recipient.

**Key Features:**
- Each account can use a **different email provider** with its own IMAP/SMTP server configuration
- Supports both **IMAP** and **POP3** protocols (configurable per account)
- Mix Gmail, Outlook, Yahoo, and custom servers in the same report

## Prerequisites

### 1. Python Environment

Ensure your virtual environment is activated:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# You should see (.venv) in your prompt
```

### 2. Required Dependencies

All dependencies should already be installed. Verify with:

```powershell
pip list | Select-String -Pattern "pandas|openpyxl|xlsxwriter"
```

If missing, install them:

```powershell
pip install pandas openpyxl xlsxwriter
```

### 3. Gmail App Passwords

**Important:** For Gmail accounts, you MUST use App Passwords, not your regular password.

#### Generate Gmail App Password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Visit [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and generate a password
5. Copy the 16-character password (no spaces)

## Configuration

### Required Environment Variables

Set these environment variables before running the script:

```powershell
# --- Source Accounts (accounts to read emails from) ---
# Each account can use a DIFFERENT email provider/server!
# You can add as many accounts as needed using ACCOUNT_1, ACCOUNT_2, ACCOUNT_3, etc.

$env:ACCOUNT_1_EMAIL="support@gmail.com"
$env:ACCOUNT_1_PASS="abcdabcdabcdabcd"  # Gmail app password
$env:ACCOUNT_1_PROTOCOL="IMAP"           # Optional: IMAP or POP3 (default: IMAP)
$env:ACCOUNT_1_SERVER="imap.gmail.com"   # Optional: defaults to imap.gmail.com for IMAP, pop.gmail.com for POP3

$env:ACCOUNT_2_EMAIL="sales@outlook.com"
$env:ACCOUNT_2_PASS="outlook-password"
$env:ACCOUNT_2_PROTOCOL="POP3"           # Use POP3 for this account
$env:ACCOUNT_2_SERVER="outlook.office365.com"  # Different server!

$env:ACCOUNT_3_EMAIL="info@company.com"
$env:ACCOUNT_3_PASS="custom-password"
$env:ACCOUNT_3_SERVER="mail.company.com"  # Custom server

# Add more accounts with any provider:
# $env:ACCOUNT_4_EMAIL="support@yahoo.com"
# $env:ACCOUNT_4_PASS="yahoo-app-password"
# $env:ACCOUNT_4_PROTOCOL="IMAP"
# $env:ACCOUNT_4_SERVER="imap.mail.yahoo.com"

# --- Sender Account (account that sends the report) ---
# Can be DIFFERENT from source accounts and use any SMTP server
$env:SENDER_EMAIL="report-bot@gmail.com"
$env:SENDER_PASS="sender-app-password"
$env:SMTP_SERVER="smtp.gmail.com"  # Optional: defaults to smtp.gmail.com
$env:SMTP_PORT="587"                # Optional: defaults to 587

# Or use a different provider for sending:
# $env:SENDER_EMAIL="bot@outlook.com"
# $env:SENDER_PASS="outlook-pass"
# $env:SMTP_SERVER="smtp.office365.com"
# $env:SMTP_PORT="587"

# --- Report Settings ---
$env:RECIPIENT_EMAIL="manager@company.com"  # Who receives the report (any email)
$env:REPORT_FILENAME="email_report.xlsx"    # Optional: output filename
$env:DAYS_BACK="7"                           # Optional: days to look back (default: 7)
```

### Choosing Between IMAP and POP3

**IMAP (Recommended - Default)**
- ✅ Keeps emails on the server
- ✅ Access from multiple devices
- ✅ Supports folders and flags
- ✅ Server-side search (faster)
- ✅ Better for ongoing monitoring
- **Use when:** You want to keep emails on the server and access them from multiple locations

**POP3 (Legacy Protocol)**
- ⚠️ Simpler protocol with fewer features
- ⚠️ Only accesses inbox (no folders)
- ⚠️ Client-side date filtering (slower for large inboxes)
- ⚠️ Messages kept on server by default (this script doesn't delete them)
- **Use when:** Server only supports POP3, or you have a specific requirement

**Default:** If you don't set `ACCOUNT_N_PROTOCOL`, IMAP is used automatically.

### Optional Advanced Settings

```powershell
# Connection timeout in seconds (default: 60)
$env:IMAP_TIMEOUT="60"

# Number of retry attempts on failure (default: 3)
$env:MAX_RETRIES="3"
```

## Running the Script

### Quick Start (Minimal Setup - Single Gmail Account)

For testing with a single account:

```powershell
# Set minimum required variables (using same Gmail account for everything)
$env:ACCOUNT_1_EMAIL="your-email@gmail.com"
$env:ACCOUNT_1_PASS="your-app-password"
$env:SENDER_EMAIL="your-email@gmail.com"
$env:SENDER_PASS="your-app-password"
$env:RECIPIENT_EMAIL="your-email@gmail.com"

# Run the script
python reporting/email_report.py
```

### Quick Start (Multiple Providers)

Testing with different email providers:

```powershell
# Read from Gmail
$env:ACCOUNT_1_EMAIL="source@gmail.com"
$env:ACCOUNT_1_PASS="gmail-app-password"
$env:ACCOUNT_1_SERVER="imap.gmail.com"

# Read from Outlook
$env:ACCOUNT_2_EMAIL="source@outlook.com"
$env:ACCOUNT_2_PASS="outlook-password"
$env:ACCOUNT_2_SERVER="outlook.office365.com"

# Send via Gmail
$env:SENDER_EMAIL="sender@gmail.com"
$env:SENDER_PASS="gmail-sender-password"
$env:RECIPIENT_EMAIL="manager@gmail.com"

# Run the script
python reporting/email_report.py
```

### Full Production Setup

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Set all environment variables (see Configuration section above)
$env:ACCOUNT_1_EMAIL="support@gmail.com"
$env:ACCOUNT_1_PASS="app-password-here"
# ... (set all variables)

# 3. Run the script
python reporting/email_report.py
```

## Expected Output

### Console Output

You'll see detailed progress information:

```
2026-01-16 10:30:00 - INFO - ============================================================
2026-01-16 10:30:00 - INFO - Email Report Generator - Starting
2026-01-16 10:30:00 - INFO - ============================================================
2026-01-16 10:30:00 - INFO - Configuration:
2026-01-16 10:30:00 - INFO -   • Discovered 2 source account(s)
2026-01-16 10:30:00 - INFO -   • Report period: Last 7 day(s)
2026-01-16 10:30:00 - INFO -   • Recipient: manager@company.com
2026-01-16 10:30:00 - INFO -   • Timeout: 60s, Max retries: 3
2026-01-16 10:30:00 - INFO - 
2026-01-16 10:30:00 - INFO - [1/2] Processing account: support@gmail.com
2026-01-16 10:30:01 - INFO - Connecting to support@gmail.com at imap.gmail.com...
2026-01-16 10:30:02 - INFO - Successfully connected to support@gmail.com
2026-01-16 10:30:02 - INFO - Found 25 email(s) in support@gmail.com
2026-01-16 10:30:03 - INFO -   Processing 10/25 emails from support@gmail.com...
2026-01-16 10:30:04 - INFO -   Processing 20/25 emails from support@gmail.com...
2026-01-16 10:30:05 - INFO - ✓ Successfully processed 25 emails from support@gmail.com
...
2026-01-16 10:30:15 - INFO - ✓ Report sent successfully!
2026-01-16 10:30:15 - INFO - ✓ Report generation completed successfully!
```

### Generated Files

1. **Excel Report**: `email_report.xlsx` (or your custom filename)
   - Contains columns: Source Account, Date, Sender, Subject
   - Auto-sized columns for easy reading

2. **Log File**: `email_report.log`
   - Detailed execution log for troubleshooting
   - Includes timestamps and error details

## Troubleshooting

### Error: "Email credentials not configured"

**Solution:** Set required environment variables:
```powershell
$env:SENDER_EMAIL="your-email@gmail.com"
$env:SENDER_PASS="your-app-password"
```

### Error: "No source accounts configured"

**Solution:** Set at least one source account:
```powershell
$env:ACCOUNT_1_EMAIL="source@gmail.com"
$env:ACCOUNT_1_PASS="app-password"
```

### Error: "IMAP authentication failed"

**Causes:**
- Using regular password instead of App Password
- Incorrect App Password
- 2-Step Verification not enabled

**Solution:**
1. Enable 2-Step Verification in Google Account
2. Generate a new App Password
3. Use the 16-character App Password (no spaces)

### Error: "Connection timeout"

**Solution:** Increase timeout or check internet connection:
```powershell
$env:IMAP_TIMEOUT="120"  # Increase to 120 seconds
```

### Error: "Permission denied" or "Invalid credentials"

**Check:**
- App Password is correct (no typos, no spaces)
- Account has IMAP enabled (Gmail Settings → Forwarding and POP/IMAP)
- 2-Step Verification is enabled

### Script runs but no emails found

**Check:**
- `DAYS_BACK` setting - you might need to increase it:
  ```powershell
  $env:DAYS_BACK="30"  # Look back 30 days
  ```
- Emails exist in the inbox (not in other folders)
- Date format compatibility with IMAP server

## Multi-Provider Configuration Examples

### Example 1: Mixed Providers (Gmail + Outlook + Custom)

**Read emails from 3 different providers, send report via Gmail:**

```powershell
# Source 1: Gmail account
$env:ACCOUNT_1_EMAIL="support@gmail.com"
$env:ACCOUNT_1_PASS="gmail-app-password"
$env:ACCOUNT_1_SERVER="imap.gmail.com"

# Source 2: Microsoft 365/Outlook account
$env:ACCOUNT_2_EMAIL="sales@outlook.com"
$env:ACCOUNT_2_PASS="outlook-password"
$env:ACCOUNT_2_SERVER="outlook.office365.com"

# Source 3: Custom domain email
$env:ACCOUNT_3_EMAIL="info@company.com"
$env:ACCOUNT_3_PASS="custom-password"
$env:ACCOUNT_3_SERVER="mail.company.com"

# Send report via Gmail
$env:SENDER_EMAIL="bot@gmail.com"
$env:SENDER_PASS="gmail-sender-password"
$env:SMTP_SERVER="smtp.gmail.com"
$env:SMTP_PORT="587"

$env:RECIPIENT_EMAIL="manager@company.com"
```

### Example 2: All Outlook Accounts

```powershell
# Multiple Outlook accounts
$env:ACCOUNT_1_EMAIL="user1@outlook.com"
$env:ACCOUNT_1_PASS="password1"
$env:ACCOUNT_1_SERVER="outlook.office365.com"

$env:ACCOUNT_2_EMAIL="user2@hotmail.com"
$env:ACCOUNT_2_PASS="password2"
$env:ACCOUNT_2_SERVER="outlook.office365.com"

# Send via Outlook
$env:SENDER_EMAIL="bot@outlook.com"
$env:SENDER_PASS="sender-password"
$env:SMTP_SERVER="smtp.office365.com"
$env:SMTP_PORT="587"

$env:RECIPIENT_EMAIL="manager@outlook.com"
```

### Example 3: Corporate Email System

```powershell
# Read from corporate Exchange accounts
$env:ACCOUNT_1_EMAIL="support@company.com"
$env:ACCOUNT_1_PASS="corp-password-1"
$env:ACCOUNT_1_SERVER="mail.company.com"

$env:ACCOUNT_2_EMAIL="sales@company.com"
$env:ACCOUNT_2_PASS="corp-password-2"
$env:ACCOUNT_2_SERVER="mail.company.com"

# Send report via corporate SMTP
$env:SENDER_EMAIL="noreply@company.com"
$env:SENDER_PASS="smtp-password"
$env:SMTP_SERVER="smtp.company.com"
$env:SMTP_PORT="587"

$env:RECIPIENT_EMAIL="reports@company.com"
```

### Example 4: Yahoo Mail

```powershell
$env:ACCOUNT_1_EMAIL="user@yahoo.com"
$env:ACCOUNT_1_PASS="yahoo-app-password"
$env:ACCOUNT_1_SERVER="imap.mail.yahoo.com"

$env:SENDER_EMAIL="sender@yahoo.com"
$env:SENDER_PASS="yahoo-sender-password"
$env:SMTP_SERVER="smtp.mail.yahoo.com"
$env:SMTP_PORT="587"
```

### Example 5: Using POP3 Protocol

```powershell
# Use POP3 for an old email system that doesn't support IMAP
$env:ACCOUNT_1_EMAIL="legacy@oldmail.com"
$env:ACCOUNT_1_PASS="legacy-password"
$env:ACCOUNT_1_PROTOCOL="POP3"
$env:ACCOUNT_1_SERVER="pop.oldmail.com"

# Mix with IMAP account
$env:ACCOUNT_2_EMAIL="modern@gmail.com"
$env:ACCOUNT_2_PASS="gmail-app-password"
$env:ACCOUNT_2_PROTOCOL="IMAP"  # Optional - IMAP is default
$env:ACCOUNT_2_SERVER="imap.gmail.com"

# Send via Gmail
$env:SENDER_EMAIL="sender@gmail.com"
$env:SENDER_PASS="gmail-sender-password"
$env:SMTP_SERVER="smtp.gmail.com"
$env:SMTP_PORT="587"

$env:RECIPIENT_EMAIL="manager@company.com"
```

## Common IMAP/SMTP Server Settings

### Gmail
- **IMAP Server:** `imap.gmail.com` (Port: 993)
- **POP3 Server:** `pop.gmail.com` (Port: 995)
- **SMTP Server:** `smtp.gmail.com` (Port: 587)
- **Note:** Requires App Passwords (see Prerequisites)

### Microsoft 365 / Outlook
- **IMAP Server:** `outlook.office365.com` (Port: 993)
- **POP3 Server:** `outlook.office365.com` (Port: 995)
- **SMTP Server:** `smtp.office365.com` (Port: 587)
- **Alternative for older accounts:** `imap-mail.outlook.com` / `pop-mail.outlook.com` / `smtp-mail.outlook.com`

### Yahoo Mail
- **IMAP Server:** `imap.mail.yahoo.com` (Port: 993)
- **POP3 Server:** `pop.mail.yahoo.com` (Port: 995)
- **SMTP Server:** `smtp.mail.yahoo.com` (Port: 587)
- **Note:** Requires App Passwords

### iCloud Mail
- **IMAP Server:** `imap.mail.me.com` (Port: 993)
- **SMTP Server:** `smtp.mail.me.com` (Port: 587)
- **Note:** Requires App-Specific Password

### AOL Mail
- **IMAP Server:** `imap.aol.com` (Port: 993)
- **SMTP Server:** `smtp.aol.com` (Port: 587)

### Zoho Mail
- **IMAP Server:** `imap.zoho.com` (Port: 993)
- **SMTP Server:** `smtp.zoho.com` (Port: 587)

### GMX Mail
- **IMAP Server:** `imap.gmx.com` (Port: 993)
- **SMTP Server:** `smtp.gmx.com` (Port: 587)

### Custom/Corporate Servers
- Contact your IT department or email provider for specific server addresses
- Common patterns:
  - IMAP: `imap.yourdomain.com` or `mail.yourdomain.com`
  - SMTP: `smtp.yourdomain.com` or `mail.yourdomain.com`
- Default ports: IMAP 993 (SSL), SMTP 587 (TLS)

## Persistent Configuration (Optional)

To avoid setting environment variables every time, you can:

### Option 1: Use a .env file (Recommended)

1. Install python-dotenv:
   ```powershell
   pip install python-dotenv
   ```

2. Copy `.env.example` to `.env`:
   ```powershell
   cp .env.example .env
   ```

3. Edit `.env` with your credentials:
   ```
   ACCOUNT_1_EMAIL=support@gmail.com
   ACCOUNT_1_PASS=your-app-password
   SENDER_EMAIL=bot@gmail.com
   SENDER_PASS=sender-app-password
   RECIPIENT_EMAIL=manager@company.com
   ```

4. Add to the top of `reporting/email_report.py`:
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Add this before other imports
   ```

### Option 2: PowerShell Profile

Add variables to your PowerShell profile:

```powershell
# Edit your profile
notepad $PROFILE

# Add these lines to the file:
$env:ACCOUNT_1_EMAIL="support@gmail.com"
$env:ACCOUNT_1_PASS="app-password"
# ... (add all variables)
```

## Scheduling (Automated Runs)

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
   - Program: `C:\workspace\congenial-octo-telegram\.venv\Scripts\python.exe`
   - Arguments: `reporting\email_report.py`
   - Start in: `C:\workspace\congenial-octo-telegram`
5. Before finishing, check "Open Properties"
6. In Properties → Actions → Edit:
   - Add environment variables in "Start in" or use a .bat wrapper script

### Batch Script Wrapper

Create `run_email_report.bat`:

```batch
@echo off
cd /d C:\workspace\congenial-octo-telegram
call .venv\Scripts\activate.bat

REM Set environment variables
set ACCOUNT_1_EMAIL=support@gmail.com
set ACCOUNT_1_PASS=app-password
set SENDER_EMAIL=bot@gmail.com
set SENDER_PASS=sender-app-password
set RECIPIENT_EMAIL=manager@company.com

REM Run the script
python reporting\email_report.py

pause
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use .env files** and add `.env` to `.gitignore` (already configured)
3. **Rotate App Passwords** periodically
4. **Use separate accounts** for automated tasks (bot accounts)
5. **Limit permissions** - bot accounts should only have necessary access
6. **Review logs** regularly in `email_report.log`

## Getting Help

- Check `email_report.log` for detailed error messages
- Verify all environment variables are set: `Get-ChildItem Env: | Where-Object { $_.Name -match "ACCOUNT|SENDER" }`
- Test individual accounts first before running all accounts
- Enable debug logging if needed (check script configuration)

## Support

For issues or questions:
1. Review the troubleshooting section above
2. Check the log file: `email_report.log`
3. Verify environment variables are correctly set
4. Ensure Gmail App Passwords are properly configured
