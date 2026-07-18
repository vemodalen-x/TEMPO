[CmdletBinding()]
param(
    [string]$TempoRoot = "",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($TempoRoot)) {
    $TempoRoot = Split-Path -Parent $PSScriptRoot
}
$TempoRoot = [IO.Path]::GetFullPath($TempoRoot)
$PythonExe = (Get-Command python.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$TempoCli = Join-Path $TempoRoot "bin\tempo"
$ConfigPath = Join-Path $TempoRoot "config\tempo.config.json"
$FreezePath = Join-Path $TempoRoot "governance\feature-freeze.json"
$PolicyPath = Join-Path $TempoRoot "plan\readiness-policy.json"
$BriefPath = Join-Path $TempoRoot "plan\decision-brief.json"
$CharterPath = Join-Path $TempoRoot "plan\mvp-charter.json"
$TaskPath = Join-Path $TempoRoot "tasks\T-20260719-TEMPO-STABILIZATION.json"
$ActivePath = Join-Path $TempoRoot ".tempo\run\active.json"
$LedgerPath = Join-Path $TempoRoot ".tempo\ledger.jsonl"

$Human = "human:repository-owner"
$HumanSession = "tty:tempo-stabilization-20260719"
$Agent = "agent:codex"
$AgentSession = "codex:tempo-stabilization-20260719"
$MvpId = "M-TEMPO-STABILIZATION-001"
$TaskId = "T-20260719-TEMPO-STABILIZATION"
$Lane = "critical-stabilization"
$Action = "implementation_write"
$StartPath = "src/tempo/warrant.py"

$CriticalPaths = @(
    "src/tempo/warrant.py",
    "src/tempo/guards.py",
    "src/tempo/demo.py",
    "src/tempo/selfcheck.py",
    "src/tempo/state.py",
    "src/tempo/ledger.py",
    "src/tempo/schema.py",
    "src/tempo/config.py",
    "src/tempo/verify.py",
    "src/tempo/lease.py",
    "src/tempo/subject.py",
    "src/tempo/transaction.py",
    "src/tempo/task.py",
    "tests/test_authorization.py",
    "tests/test_guards.py",
    "tests/test_conformance.py",
    "tests/test_ledger.py",
    "tests/test_verify.py",
    "tests/test_stabilization.py",
    "schemas/ledger-event.schema.json",
    "schemas/authorization-warrant.schema.json",
    "schemas/receipt.schema.json",
    "schemas/build-lease.schema.json",
    "schemas/task.schema.json",
    "schemas/subject-repository.schema.json",
    "governance/feature-freeze.json",
    "tasks/T-20260719-TEMPO-STABILIZATION.json",
    "MANIFEST.json",
    "TRACEABILITY.md",
    "SECURITY.md",
    "README.md",
    "docs/**",
    "demo/**",
    "samples/**"
)

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function ConvertTo-Utf8Bytes {
    param([Parameter(Mandatory)]$Value)
    $json = $Value | ConvertTo-Json -Depth 100
    return [Text.UTF8Encoding]::new($false).GetBytes($json + "`n")
}

function Write-BytesAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][byte[]]$Bytes
    )
    $full = [IO.Path]::GetFullPath($Path)
    $directory = [IO.Path]::GetDirectoryName($full)
    if ([string]::IsNullOrWhiteSpace($directory) -or -not [IO.Directory]::Exists($directory)) {
        throw "Atomic write directory is invalid: $directory"
    }
    $name = [IO.Path]::GetFileName($full)
    $temp = Join-Path $directory (".$name.tmp." + [Guid]::NewGuid().ToString("N"))
    $backup = Join-Path $directory (".$name.bak." + [Guid]::NewGuid().ToString("N"))
    try {
        [IO.File]::WriteAllBytes($temp, $Bytes)
        if ([IO.File]::Exists($full)) {
            [IO.File]::Replace($temp, $full, $backup, $true)
            if ([IO.File]::Exists($backup)) { [IO.File]::Delete($backup) }
        }
        else {
            [IO.File]::Move($temp, $full)
        }
    }
    finally {
        if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
        if ([IO.File]::Exists($backup)) { [IO.File]::Delete($backup) }
    }
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )
    Write-BytesAtomic -Path $Path -Bytes (ConvertTo-Utf8Bytes $Value)
}

function Invoke-TempoJson {
    param(
        [Parameter(Mandatory)][string]$Actor,
        [Parameter(Mandatory)][string]$Session,
        [Parameter(Mandatory)][string[]]$Arguments
    )
    $output = & $PythonExe $TempoCli --root $TempoRoot --actor $Actor --session $Session --json @Arguments 2>&1
    $exit = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ($exit -ne 0) {
        throw "TEMPO command failed ($exit): $text"
    }
    try { return $text | ConvertFrom-Json }
    catch { throw "TEMPO returned non-JSON output: $text" }
}

foreach ($required in @($TempoCli, $ConfigPath, $FreezePath, $PolicyPath, $BriefPath, $CharterPath, $TaskPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file is missing: $required"
    }
}

$policy = Read-JsonFile $PolicyPath
$brief = Read-JsonFile $BriefPath
$charter = Read-JsonFile $CharterPath
$config = Read-JsonFile $ConfigPath
$freeze = Read-JsonFile $FreezePath

if ($policy.policy_id -ne "RP-TEMPO-STABILIZATION-001" -or
    $brief.decision_brief_id -ne "DB-TEMPO-STABILIZATION-001" -or
    $charter.mvp_id -ne $MvpId) {
    throw "The stabilization records do not match the expected IDs."
}

$alreadyApproved =
    $policy.state -eq "signed" -and
    $brief.state -eq "signed" -and
    $config.guards.post_freeze_critical_fix.task_id -eq $TaskId

Write-Host ""
Write-Host "TEMPO critical stabilization" -ForegroundColor Cyan
Write-Host "P0-1: authorize-only implementation writes are currently allowed."
Write-Host "P0-2: a rejected start can leave BUILDING + active.json without mvp_started."
Write-Host "Scope: three bounded cycles; no deployment, publication, video upload, or Devpost submission."
Write-Host "Budget cap: 1 USD; projected external spend: 0 USD; deadline: $($charter.deadline)."
Write-Warning "This is a human policy action. It adds only the listed post-freeze critical-fix paths; the warrant and start gate still apply."

if (-not $alreadyApproved) {
    if ($policy.state -ne "draft" -or $brief.state -ne "draft") {
        throw "Policy and brief are in a mixed state; inspect them before continuing."
    }
    $phrase = "APPROVE RP-TEMPO-STABILIZATION-001 DB-TEMPO-STABILIZATION-001 AND FREEZE EXCEPTION $TaskId"
    if ($ValidateOnly) {
        Write-Host "Preflight passed. No signer-owned record was changed." -ForegroundColor Green
        exit 0
    }
    $answer = (Read-Host "Type this exact approval phrase: $phrase").Trim()
    if ($answer -cne $phrase) {
        throw "Approval phrase did not match. No signer-owned record was changed."
    }

    $approvedAt = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    $configOriginal = [IO.File]::ReadAllBytes($ConfigPath)
    $freezeOriginal = [IO.File]::ReadAllBytes($FreezePath)
    $policyOriginal = [IO.File]::ReadAllBytes($PolicyPath)
    $briefOriginal = [IO.File]::ReadAllBytes($BriefPath)

    $freezeAllow = [Collections.Generic.List[string]]::new()
    foreach ($path in @($config.guards.freeze_allow) + $CriticalPaths) {
        if (-not $freezeAllow.Contains([string]$path)) { $freezeAllow.Add([string]$path) }
    }
    $config.guards.freeze_allow = @($freezeAllow)
    $config.guards | Add-Member -Force -NotePropertyName post_freeze_critical_fix -NotePropertyValue ([pscustomobject]@{
        task_id = $TaskId
        mvp_id = $MvpId
        allowed_paths = $CriticalPaths
        approved_by = $Human
        approved_at = $approvedAt
        signing_provenance = "tty_human"
        expires_at = $charter.deadline
    })

    $freeze | Add-Member -Force -NotePropertyName pending_critical_fix_authorization -NotePropertyValue ([pscustomobject]@{
        task_id = $TaskId
        mvp_id = $MvpId
        reason = "Start-bound authority, lifecycle failure atomicity, strict task validation, and subject-repository binding"
        allowed_paths = $CriticalPaths
        approved_by = $Human
        approved_at = $approvedAt
        signing_provenance = "tty_human"
        status = "authorized_pending_verification"
    })

    $policy.state = "signed"
    $policy.approved_by = $Human
    $policy.approved_at = $approvedAt
    $brief.state = "signed"
    $brief.approved_by = $Human
    $brief.approved_at = $approvedAt
    $brief.signing_provenance = "tty_human"
    $brief.updated_at = $approvedAt

    try {
        Write-JsonAtomic $ConfigPath $config
        Write-JsonAtomic $FreezePath $freeze
        Write-JsonAtomic $PolicyPath $policy
        Write-JsonAtomic $BriefPath $brief
    }
    catch {
        Write-BytesAtomic $ConfigPath $configOriginal
        Write-BytesAtomic $FreezePath $freezeOriginal
        Write-BytesAtomic $PolicyPath $policyOriginal
        Write-BytesAtomic $BriefPath $briefOriginal
        throw
    }
    Write-Host "Policy, brief, and narrow freeze exception recorded at $approvedAt." -ForegroundColor Green
}
else {
    $resume = "RESUME $MvpId"
    if ($ValidateOnly) {
        Write-Host "Preflight passed. No signer-owned record was changed." -ForegroundColor Green
        exit 0
    }
    $answer = (Read-Host "Signed records detected. Type this exact resume phrase: $resume").Trim()
    if ($answer -cne $resume) { throw "Resume phrase did not match." }
}

$charter = Read-JsonFile $CharterPath
if ($charter.state -eq "draft") {
    Write-Host "When TEMPO prompts, type this exact phrase:" -ForegroundColor Yellow
    Write-Host "SIGN $MvpId" -ForegroundColor Yellow
    & $PythonExe $TempoCli --root $TempoRoot --actor $Human --session $HumanSession mvp sign-charter --signer $Human
    if ($LASTEXITCODE -ne 0) { throw "TEMPO charter signing failed." }
}

$assessment = Invoke-TempoJson -Actor $Human -Session $HumanSession -Arguments @("mvp", "assess")
if ($assessment.primary_outcome -ne "MVP_AUTHORIZED" -or
    $assessment.eligible_for_authorization -ne $true -or
    @($assessment.hard_blockers).Count -ne 0 -or
    @($assessment.floor_failures).Count -ne 0 -or
    $assessment.rank_one_threshold.status -ne "passed") {
    $assessment | ConvertTo-Json -Depth 100 | Write-Host
    throw "Fresh assessment is not eligible for authorization."
}
Write-Host "Fresh assessment $($assessment.assessment_id), score $($assessment.weighted_score)." -ForegroundColor Green

$status = Invoke-TempoJson -Actor $Human -Session $HumanSession -Arguments @("mvp", "status")
if (-not $status.authorization_valid) {
    Write-Host "When TEMPO prompts, type this exact phrase:" -ForegroundColor Yellow
    Write-Host "AUTHORIZE $MvpId $($assessment.assessment_hash)" -ForegroundColor Yellow
    & $PythonExe $TempoCli --root $TempoRoot --actor $Human --session $HumanSession mvp authorize --assessment-hash $assessment.assessment_hash --signer $Human --ttl-hours 24
    if ($LASTEXITCODE -ne 0) { throw "TEMPO warrant authorization failed." }
    $status = Invoke-TempoJson -Actor $Human -Session $HumanSession -Arguments @("mvp", "status")
}
if (-not $status.authorization_valid -or $status.mvp_state -notin @("AUTHORIZED", "BUILDING")) {
    throw "No current human warrant is available."
}

if ($status.mvp_state -ne "BUILDING") {
    $started = Invoke-TempoJson -Actor $Agent -Session $AgentSession -Arguments @(
        "mvp", "start",
        "--task", $TaskId,
        "--path", $StartPath,
        "--lane", $Lane,
        "--action", $Action
    )
    if (-not $started.ok) { throw "TEMPO start did not succeed." }
}

$final = Invoke-TempoJson -Actor $Agent -Session $AgentSession -Arguments @("mvp", "status")
$ledger = Invoke-TempoJson -Actor $Agent -Session $AgentSession -Arguments @("ledger", "verify")
$active = Read-JsonFile $ActivePath
$events = @(Get-Content -LiteralPath $LedgerPath -Encoding UTF8 | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
$matchingStarts = @($events | Where-Object {
    $_.event_type -eq "mvp_started" -and
    $_.relevant_ids.task_id -eq $TaskId -and
    $_.relevant_ids.warrant_id -eq $active.warrant_id -and
    $_.details.lane -eq $Lane -and
    $_.details.action -eq $Action -and
    $_.details.path -eq $StartPath
})

if (-not $final.authorization_valid -or $final.mvp_state -ne "BUILDING" -or
    -not $ledger.ok -or $ledger.outcome -ne "LEDGER_VALID" -or
    $active.task_id -ne $TaskId -or $active.lane -ne $Lane -or
    $active.action -ne $Action -or $active.path -ne $StartPath -or
    $matchingStarts.Count -ne 1) {
    throw "Final state, active lease, and ledger start are not exactly consistent."
}

Write-Host ""
Write-Host "TEMPO stabilization authority is active." -ForegroundColor Green
Write-Host "Warrant: $($final.warrant_id)"
Write-Host "Expires: $($final.expires_at)"
Write-Host "Task: $TaskId"
Write-Host "Start event: $($matchingStarts[0].event_id)"
Write-Host "The script authorized development only; it did not publish, deploy, upload, or submit anything."
