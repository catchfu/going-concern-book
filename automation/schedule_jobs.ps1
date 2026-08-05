<#
.SYNOPSIS
    Sets up Windows Task Scheduler jobs for automated KPMG scandal research.

.DESCRIPTION
    Creates scheduled tasks using schtasks.exe (compatible with all Windows versions):

    Task                          Schedule          Purpose
    ---                           ---               ---
    KPMG_Research_WeeklyNewsFetch  Mon 9AM           Auto-fetch news articles
    KPMG_Research_BiweeklyFOICheck 1st 10AM          FOI status reminder
    KPMG_Research_BiweeklyFOICheck_15 15th 10AM      FOI status reminder
    KPMG_Research_DailyHansardCheck  Weekdays 6PM    Hansard transcript monitor
    KPMG_Research_MonthlyReview    1st 2PM           Monthly progress review
    KPMG_Research_CapgeminiMonitor  Fri 11AM         Defence deal tracking
    KPMG_Research_InterviewOutreach Wed 10AM         Interview scheduling

.NOTES
    Run as Administrator. Uses schtasks.exe (built-in, no module required).
#>

param(
    [string]$ProjectPath = "C:\QQ\Projects\audit_scanda"
)

$ErrorActionPreference = "Continue"

Write-Host "Setting up KPMG Audit Scandal Research Scheduled Jobs..."
Write-Host "Project Path: $ProjectPath"
Write-Host "Python Path: $((Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source) -or 'python')"
Write-Host ""

$tasks = @(
    # TaskName, ScheduleType, DayOrDays, Time, Executable, Arguments
    @("WeeklyNewsFetch", "WEEKLY", "MON", "09:00", "cmd.exe",
      "/c `"$ProjectPath\automation\run_weekly.bat`""),

    @("BiweeklyFOICheck", "MONTHLY", "1", "10:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && echo FOI Check Due: Finance, Treasury, ASIC, NSW FOI portals && pause"),

    @("BiweeklyFOICheck_15", "MONTHLY", "15", "10:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && echo FOI Check Due: Finance, Treasury, ASIC, NSW FOI portals && pause"),

    @("DailyHansardCheck", "WEEKLY", "MON,TUE,WED,THU,FRI", "18:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && powershell -File `"$ProjectPath\automation\check_hansard.ps1`""),

    @("MonthlyReview", "MONTHLY", "1", "14:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && start notepad.exe `"$ProjectPath\RESEARCH_TRACKING.md`" && pause"),

    @("CapgeminiMonitor", "WEEKLY", "FRI", "11:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && echo Check: Capgemini ASX, KPMG press, AFR for deal updates && pause"),

    @("InterviewOutreach", "WEEKLY", "WED", "10:00", "cmd.exe",
      "/c cd /d `"$ProjectPath`" && echo Interview Outreach: Contact targets from Tier 5 list && echo See RESEARCH_TRACKING.md && pause")
)

foreach ($t in $tasks) {
    $taskName = "KPMG_Research_$($t[0])"
    $schedule = $t[1]
    $dayArg = $t[2]
    $time = $t[3]
    $exec = $t[4]
    $taskArgs = $t[5]

    if ($schedule -eq "WEEKLY") {
        $dayFlag = "/d $dayArg"
    }
    elseif ($schedule -eq "MONTHLY") {
        $dayFlag = if ($dayArg -match '^\d+$' -and [int]$dayArg -le 31) { "/d $dayArg" } else { "/d LAST" }
    }
    else {
        $dayFlag = ""
    }

    # Build /tr value with proper quoting: use single quotes for schtasks, double for inner
    $trValue = "$exec $taskArgs"
    $argList = @("/create", "/tn", $taskName, "/tr", $trValue, "/sc", $schedule)
    if ($dayFlag) { $argList += @("/d", $dayArg) }
    $argList += @("/st", $time, "/f")

    Write-Host "Creating: $taskName ($schedule $time)"
    & "schtasks" $argList 2>&1 | Out-Null

    if ($?) {
        Write-Host "  OK"
    } else {
        Write-Host "  FAILED (may already exist or need Admin rights)"
    }
}

Write-Host ""
Write-Host "Done. Created/updated $($tasks.Count) tasks."
Write-Host ""
Write-Host "To verify: schtasks /query /v | findstr KPMG_Research"
Write-Host "To run now: schtasks /run /tn KPMG_Research_WeeklyNewsFetch"
Write-Host "To delete:  schtasks /delete /tn KPMG_Research_WeeklyNewsFetch /f"