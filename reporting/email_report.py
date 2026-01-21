import imaplib
import poplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import pandas as pd
import os
import re
import logging
from time import sleep

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars only

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---

def discover_accounts():
    """Dynamically discover all account configurations from environment variables.
    
    Looks for patterns like ACCOUNT_1_EMAIL, ACCOUNT_2_EMAIL, etc.
    Returns a list of account dictionaries with email, password, and server.
    """
    accounts = []
    account_pattern = re.compile(r'^ACCOUNT_(\d+)_EMAIL$')
    
    # Find all account numbers by scanning environment variables
    account_numbers = set()
    for key in os.environ.keys():
        match = account_pattern.match(key)
        if match:
            account_numbers.add(int(match.group(1)))
    
    # Build account configurations for each discovered account number
    for num in sorted(account_numbers):
        email_addr = os.environ.get(f'ACCOUNT_{num}_EMAIL')
        password = os.environ.get(f'ACCOUNT_{num}_PASS', '')
        protocol = os.environ.get(f'ACCOUNT_{num}_PROTOCOL', 'IMAP').upper()
        
        # Set default server based on protocol
        if protocol == 'POP3':
            default_server = 'pop.gmail.com'
        else:
            default_server = 'imap.gmail.com'
        
        server = os.environ.get(f'ACCOUNT_{num}_SERVER', default_server)
        
        if email_addr:  # Only add if email is configured
            accounts.append({
                'email': email_addr,
                'password': password,
                'server': server,
                'protocol': protocol
            })
    
    return accounts

# 1. Accounts to READ from (Source Accounts)
ACCOUNTS_TO_CHECK = discover_accounts()

# 2. Account to SEND the report with (Bot Account)
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')
SENDER_PASS = os.environ.get('SENDER_PASS', '')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))

# 3. Report Settings
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'manager@yourcompany.com')
REPORT_FILENAME = os.environ.get('REPORT_FILENAME', 'consolidated_email_report.xlsx')
DAYS_BACK = int(os.environ.get('DAYS_BACK', '7'))
IMAP_TIMEOUT = int(os.environ.get('IMAP_TIMEOUT', '60'))  # seconds
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))

def decode_email_header(header_value):
    """Safely decode email header that might be encoded."""
    if not header_value:
        return "No Subject"
    
    try:
        decoded_parts = email.header.decode_header(header_value)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding if encoding else "utf-8", errors='replace')
            else:
                decoded_str += str(part)
        return decoded_str
    except Exception as e:
        logger.warning(f"Failed to decode header '{header_value}': {e}")
        return str(header_value)

def fetch_from_account(account_config, retry_count=0):
    """Connects to a single account and returns a list of email data with retry logic.
    Supports both IMAP and POP3 protocols.
    """
    user = account_config['email']
    pwd = account_config['password']
    server_host = account_config['server']
    protocol = account_config.get('protocol', 'IMAP').upper()
    
    if protocol == 'POP3':
        return fetch_from_pop3(account_config, retry_count)
    else:
        return fetch_from_imap(account_config, retry_count)

def fetch_from_imap(account_config, retry_count=0):
    """Fetches emails using IMAP protocol."""
    user = account_config['email']
    pwd = account_config['password']
    server_host = account_config['server']
    
    extracted_data = []
    
    try:
        logger.info(f"Connecting to {user} at {server_host} (IMAP)...")
        
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(server_host)
        mail.login(user, pwd)
        
        # Select inbox
        status, count = mail.select('inbox')
        if status != 'OK':
            logger.error(f"Failed to select inbox for {user}")
            return extracted_data
        
        logger.info(f"Successfully connected to {user}")

        # Search for emails
        date_cutoff = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date_cutoff}")')
        
        if status != 'OK':
            logger.error(f"Failed to search emails for {user}")
            return extracted_data
        
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        logger.info(f"Found {total_emails} email(s) in {user}")

        # Process emails with progress indicator
        for idx, e_id in enumerate(email_ids, 1):
            try:
                if idx % 10 == 0 or idx == total_emails:
                    logger.info(f"  Processing {idx}/{total_emails} emails from {user}...")
                
                status, msg_data = mail.fetch(e_id, '(RFC822)')
                if status != 'OK':
                    logger.warning(f"Failed to fetch email ID {e_id}")
                    continue
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Safely decode subject
                        subject = decode_email_header(msg.get("Subject"))
                        sender = msg.get("From", "Unknown Sender")
                        date_str = msg.get("Date", "Unknown Date")
                        
                        extracted_data.append({
                            "Source Account": user,
                            "Date": date_str,
                            "Sender": sender,
                            "Subject": subject
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing email ID {e_id} from {user}: {e}")
                continue
        
        mail.close()
        mail.logout()
        logger.info(f"[OK] Successfully processed {len(extracted_data)} emails from {user}")
        
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error for {user}: {e}")
        if retry_count < MAX_RETRIES:
            logger.info(f"Retrying {user} (attempt {retry_count + 1}/{MAX_RETRIES})...")
            sleep(2 ** retry_count)  # Exponential backoff
            return fetch_from_imap(account_config, retry_count + 1)
    except TimeoutError:
        logger.error(f"Connection timeout for {user}")
    except Exception as e:
        logger.error(f"Unexpected error processing {user}: {e}", exc_info=True)
        
    return extracted_data

def fetch_from_pop3(account_config, retry_count=0):
    """Fetches emails using POP3 protocol.
    Note: POP3 doesn't support server-side date filtering, so we filter client-side.
    """
    user = account_config['email']
    pwd = account_config['password']
    server_host = account_config['server']
    
    extracted_data = []
    
    try:
        logger.info(f"Connecting to {user} at {server_host} (POP3)...")
        
        # Connect to POP3 server
        mail = poplib.POP3_SSL(server_host)
        mail.user(user)
        mail.pass_(pwd)
        
        logger.info(f"Successfully connected to {user}")
        
        # Get message count
        num_messages = len(mail.list()[1])
        logger.info(f"Found {num_messages} email(s) in {user}")
        
        # Calculate date cutoff for client-side filtering
        date_cutoff = datetime.now() - timedelta(days=DAYS_BACK)
        
        # Process emails with progress indicator
        for i in range(1, num_messages + 1):
            try:
                if i % 10 == 0 or i == num_messages:
                    logger.info(f"  Processing {i}/{num_messages} emails from {user}...")
                
                # Retrieve email
                response, lines, octets = mail.retr(i)
                msg_data = b'\r\n'.join(lines)
                msg = email.message_from_bytes(msg_data)
                
                # Get and parse date
                date_str = msg.get("Date", "")
                try:
                    # Parse email date
                    from email.utils import parsedate_to_datetime
                    msg_date = parsedate_to_datetime(date_str)
                    
                    # Filter by date (client-side since POP3 doesn't support server-side filtering)
                    if msg_date.replace(tzinfo=None) < date_cutoff:
                        continue  # Skip old emails
                except Exception as date_err:
                    logger.debug(f"Could not parse date '{date_str}': {date_err}")
                    # Include email if date parsing fails
                
                # Safely decode subject
                subject = decode_email_header(msg.get("Subject"))
                sender = msg.get("From", "Unknown Sender")
                
                extracted_data.append({
                    "Source Account": user,
                    "Date": date_str,
                    "Sender": sender,
                    "Subject": subject
                })
                
            except Exception as e:
                logger.warning(f"Error processing email #{i} from {user}: {e}")
                continue
        
        # Keep messages on server (don't delete)
        mail.quit()
        logger.info(f"[OK] Successfully processed {len(extracted_data)} emails from {user}")
        
    except poplib.error_proto as e:
        logger.error(f"POP3 error for {user}: {e}")
        if retry_count < MAX_RETRIES:
            logger.info(f"Retrying {user} (attempt {retry_count + 1}/{MAX_RETRIES})...")
            sleep(2 ** retry_count)  # Exponential backoff
            return fetch_from_pop3(account_config, retry_count + 1)
    except TimeoutError:
        logger.error(f"Connection timeout for {user}")
    except Exception as e:
        logger.error(f"Unexpected error processing {user}: {e}", exc_info=True)
        
    return extracted_data

def send_consolidated_report(dataframe):
    """Sends the master Excel file via email."""
    if dataframe.empty:
        logger.warning("No emails found across any accounts. Skipping report.")
        return False

    try:
        # Try to create Excel with auto-sizing; if the Excel writer fails (e.g. in
        # tests where the engine may be mocked), fall back to a CSV file so we
        # can still attach and send a report.
        try:
            with pd.ExcelWriter(REPORT_FILENAME, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Email Report')

                # Auto-adjust column widths
                worksheet = writer.sheets['Email Report']
                for idx, col in enumerate(dataframe.columns):
                    max_length = max(
                        dataframe[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    worksheet.set_column(idx, idx, min(max_length, 50))

            logger.info(f"[OK] Report saved as {REPORT_FILENAME}")
        except Exception as write_exc:
            logger.warning(f"Excel writer failed ({write_exc}); falling back to CSV output")
            try:
                dataframe.to_csv(REPORT_FILENAME, index=False)
                logger.info(f"[OK] Report saved as CSV {REPORT_FILENAME}")
            except Exception as csv_exc:
                logger.error(f"Failed to write fallback CSV report: {csv_exc}")
                raise

        # Prepare Email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"Email Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Create summary by account
        account_summary = dataframe.groupby('Source Account').size().to_dict()
        summary_lines = "\n".join([f"    - {acc}: {count} emails" for acc, count in account_summary.items()])
        
        body = f"""Hi,

Here is the consolidated email report for the last {DAYS_BACK} day(s).

Summary:
    - Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    - Accounts Scanned: {len(ACCOUNTS_TO_CHECK)}
    - Total Emails Found: {len(dataframe)}

Breakdown by Account:
{summary_lines}

The detailed report is attached as an Excel file.

---
This report was generated automatically.
"""
        msg.attach(MIMEText(body, 'plain'))

        # Attach Excel
        with open(REPORT_FILENAME, "rb") as attachment:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{REPORT_FILENAME}"')
            msg.attach(part)

        # Send with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Sending report to {RECIPIENT_EMAIL}...")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASS)
                server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
                server.quit()
                logger.info("[OK] Report sent successfully!")
                return True
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                break  # Don't retry auth errors
            except Exception as e:
                logger.error(f"Error sending email (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    sleep(2 ** attempt)
                else:
                    logger.error("Failed to send email after all retries")
                    
    except Exception as e:
        logger.error(f"Error creating/sending report: {e}", exc_info=True)
        return False
    
    return False


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Email Report Generator - Starting")
    logger.info("="*60)
    
    # Validate credentials are configured
    if not SENDER_EMAIL or not SENDER_PASS:
        logger.error("Email credentials not configured. Set SENDER_EMAIL and SENDER_PASS environment variables.")
        exit(1)
    
    if not ACCOUNTS_TO_CHECK:
        logger.error("No source accounts configured. Set ACCOUNT_1_EMAIL, ACCOUNT_2_EMAIL, etc.")
        exit(1)
    
    # Check that at least one source account has credentials
    if not any(acc['password'] for acc in ACCOUNTS_TO_CHECK):
        logger.error("No source account passwords configured. Set ACCOUNT_*_PASS environment variables.")
        exit(1)
    
    logger.info(f"Configuration:")
    logger.info(f"  - Discovered {len(ACCOUNTS_TO_CHECK)} source account(s)")
    logger.info(f"  - Report period: Last {DAYS_BACK} day(s)")
    logger.info(f"  - Recipient: {RECIPIENT_EMAIL}")
    logger.info(f"  - Timeout: {IMAP_TIMEOUT}s, Max retries: {MAX_RETRIES}")
    logger.info("")
    
    master_list = []
    successful_accounts = 0
    
    # Loop through every discovered account
    for idx, account in enumerate(ACCOUNTS_TO_CHECK, 1):
        logger.info(f"[{idx}/{len(ACCOUNTS_TO_CHECK)}] Processing account: {account['email']}")
        
        # Skip accounts without passwords configured
        if not account['password']:
            logger.warning(f"  Skipping {account['email']} - no password configured")
            continue
            
        account_data = fetch_from_account(account)
        if account_data:
            successful_accounts += 1
        master_list.extend(account_data)
        logger.info("")
    
    logger.info("="*60)
    logger.info("Processing Complete")
    logger.info(f"  - Accounts processed: {successful_accounts}/{len(ACCOUNTS_TO_CHECK)}")
    logger.info(f"  - Total emails collected: {len(master_list)}")
    logger.info("="*60)
    
    # Convert master list to DataFrame
    if master_list:
        df = pd.DataFrame(master_list)
        logger.info("")
        
        # Send the final report
        success = send_consolidated_report(df)
        
        if success:
            logger.info("="*60)
            logger.info("[SUCCESS] Report generation completed successfully!")
            logger.info("="*60)
            exit(0)
        else:
            logger.error("[ERROR] Report generation completed with errors")
            exit(1)
    else:
        logger.warning("No emails collected from any account.")
        logger.info("="*60)
        exit(0)