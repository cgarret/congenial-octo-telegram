# PowerShell helper scripts

This folder contains PowerShell helpers used by the project.

load_variables.ps1
- Purpose: Load a `.env` file into the current PowerShell session as environment variables.
- Usage: Run from the project root so the script can locate `.env`:

```powershell
& .\scripts\powershell\load_variables.ps1
```

- Notes:
  - Supports quoted values (single or double quotes) and values containing `=`.
  - Discovers source accounts using `ACCOUNT_N_EMAIL` pattern.
  - The script will prompt if a `.env` is missing and should not be committed to the repository.
