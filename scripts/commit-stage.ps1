param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

if (-not $Message) {
    Write-Host "Error: Commit message required." -ForegroundColor Red
    Write-Host "Usage: .\scripts\commit-stage.ps1 'feat: describe changes'"
    exit 1
}

git add -A
git commit -m $Message
Write-Host "Committed: $Message" -ForegroundColor Green
