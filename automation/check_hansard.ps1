<#
.SYNOPSIS
    Opens APH Hansard committee pages for manual review.
    News articles about new transcripts will be caught by fetch_news.py weekly.
#>

param(
    [string]$ProjectPath = "C:\QQ\Projects\audit_scanda"
)

$ErrorActionPreference = "Continue"

Write-Host "[$(Get-Date)] Hansard Monitor"
Write-Host ""
Write-Host "Key committee pages to check for KPMG-related transcripts:"
Write-Host ""

$pages = @(
    @("PJC Corporations & Financial Services",
      "https://www.aph.gov.au/Parliamentary_Business/Committees/Joint/Corporations_and_Financial_Services"),
    @("Senate Finance & Public Admin",
      "https://www.aph.gov.au/Parliamentary_Business/Committees/Senate/Finance_and_Public_Administration"),
    @("PJC Defence (O'Neill Chair)",
      "https://www.aph.gov.au/Parliamentary_Business/Committees/Joint/Defence"),
    @("APH Hansard Search - KPMG",
      "https://parlinfo.aph.gov.au/parlInfo/search/summary/summary.w3p;query=KPMG")
)

foreach ($p in $pages) {
    Write-Host "  [$($p[0])]"
    Write-Host "    $($p[1])"
    Write-Host ""
}

# Open browser for the most relevant page
Write-Host "Opening PJC Corporations committee page in browser..."
try {
    Start-Process $pages[0][1]
} catch {
    Write-Warning "Could not open browser automatically"
}

$logFile = Join-Path $ProjectPath "sources\hansard\check_log.txt"
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Checked $($pages.Count) pages" | Add-Content $logFile
Write-Host "[$(Get-Date)] Complete. Log: $logFile"