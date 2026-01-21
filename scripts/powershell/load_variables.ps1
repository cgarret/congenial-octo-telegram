# load_variables.ps1
# Loads email report configuration variables into the current PowerShell session

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Report - Environment Loader" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

# Check for .env file
$envFile = Join-Path $projectRoot ".env"
$envExample = Join-Path $projectRoot ".env.example"

if (Test-Path $envFile) {
    Write-Host "Loading variables from .env file..." -ForegroundColor Green

    # Read and parse .env file (supports quoted values and values containing =)
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()

        # Skip empty lines and comments
        if ($line -and -not $line.StartsWith("#")) {
            $splitIndex = $line.IndexOf('=')
            if ($splitIndex -ge 0) {
                $key = $line.Substring(0, $splitIndex).Trim()
                $value = $line.Substring($splitIndex + 1).Trim()

                # Strip matching surrounding quotes
                if ((($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) -and $value.Length -ge 2) {
                    $value = $value.Substring(1, $value.Length - 2)
                }

                # Set environment variable in current process
                Set-Item -Path "env:$key" -Value $value
                Write-Host "  ✓ Loaded: $key" -ForegroundColor Gray
            }
        }
    }

    Write-Host ""
    Write-Host "✓ Environment variables loaded from .env" -ForegroundColor Green

} elseif (Test-Path $envExample) {
    Write-Host "⚠ No .env file found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Create .env file from template:" -ForegroundColor White
    Write-Host "  Copy-Item '$envExample' '.env'" -ForegroundColor Cyan
    Write-Host "  Then edit .env with your credentials" -ForegroundColor Cyan
    Write-Host ""
    exit 1

} else {
    Write-Host "⚠ No .env or .env.example file found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Set variables manually:" -ForegroundColor White
    Write-Host '  $env:ACCOUNT_1_EMAIL="your@email.com"' -ForegroundColor Cyan
    Write-Host '  $env:ACCOUNT_1_PASS="app-password"' -ForegroundColor Cyan
    Write-Host '  $env:SENDER_EMAIL="sender@email.com"' -ForegroundColor Cyan
    Write-Host '  $env:SENDER_PASS="sender-password"' -ForegroundColor Cyan
    Write-Host '  $env:RECIPIENT_EMAIL="recipient@email.com"' -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Display loaded configuration summary
Write-Host ""
Write-Host "Configuration Summary:" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Count discovered accounts
$accountCount = 0
$accountNum = 1
while ($true) {
    $emailVar = "ACCOUNT_${accountNum}_EMAIL"
    $protocolVar = "ACCOUNT_${accountNum}_PROTOCOL"

    $email = [System.Environment]::GetEnvironmentVariable($emailVar)
    if (-not $email) { break }

    $protocol = [System.Environment]::GetEnvironmentVariable($protocolVar)
    if (-not $protocol) { $protocol = "IMAP" }

    Write-Host ("  Account {0}: {1} ({2})" -f $accountNum, $email, $protocol) -ForegroundColor White
    $accountCount++
    $accountNum++
}

if ($accountCount -eq 0) {
    Write-Host "  ⚠ No source accounts configured!" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ $accountCount source account(s) configured" -ForegroundColor Green
}

# Display sender configuration
$sender = [System.Environment]::GetEnvironmentVariable('SENDER_EMAIL')
if ($sender) {
    Write-Host ("  Sender: {0}" -f $sender) -ForegroundColor White
} else {
    Write-Host "  ⚠ No sender email configured!" -ForegroundColor Yellow
}

# Display recipient
$recipient = [System.Environment]::GetEnvironmentVariable('RECIPIENT_EMAIL')
if ($recipient) {
    Write-Host ("  Recipient: {0}" -f $recipient) -ForegroundColor White
} else {
    Write-Host "  ⚠ No recipient email configured!" -ForegroundColor Yellow
}

# Display optional settings
$daysBack = [System.Environment]::GetEnvironmentVariable('DAYS_BACK')
if (-not $daysBack) { $daysBack = '7 (default)' }
Write-Host ("  Days back: {0}" -f $daysBack) -ForegroundColor Gray

Write-Host ""
Write-Host "✓ Variables loaded into current session" -ForegroundColor Green
Write-Host ""
Write-Host "Run the email report:" -ForegroundColor White
Write-Host "  python reporting/email_report.py" -ForegroundColor Cyan
Write-Host ""