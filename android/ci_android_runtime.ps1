[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$androidRoot = $PSScriptRoot
$sdkRoot = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } elseif ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "" }
if (-not $sdkRoot) { throw "ANDROID_SDK_ROOT or ANDROID_HOME is required." }
if (-not $env:RUNNER_TEMP) { throw "RUNNER_TEMP is required for emulator diagnostics." }

$adb = Join-Path $sdkRoot "platform-tools\adb.exe"
$emulator = Join-Path $sdkRoot "emulator\emulator.exe"
if (-not (Test-Path -LiteralPath $adb)) { throw "adb.exe was not found: $adb" }
if (-not (Test-Path -LiteralPath $emulator)) { throw "emulator.exe was not found: $emulator" }

function Get-OnlineEmulators {
    $result = @()
    foreach ($line in (& $adb devices)) {
        if ($line -match '^(emulator-\d+)\s+device\s*$') { $result += $Matches[1] }
    }
    return $result
}

function Write-EmulatorDiagnostics {
    Write-Host "=== Android runtime emulator diagnostics ==="
    & $adb devices -l | Out-Host
    if ($script:emulatorStdout -and (Test-Path -LiteralPath $script:emulatorStdout)) {
        Write-Host "--- emulator stdout ---"
        Get-Content -LiteralPath $script:emulatorStdout -ErrorAction SilentlyContinue | Out-Host
    }
    if ($script:emulatorStderr -and (Test-Path -LiteralPath $script:emulatorStderr)) {
        Write-Host "--- emulator stderr ---"
        Get-Content -LiteralPath $script:emulatorStderr -ErrorAction SilentlyContinue | Out-Host
    }
    Write-Host "=== End diagnostics ==="
}

function Invoke-Gradle {
    param([string[]]$Arguments)
    & .\gradlew.bat @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Gradle failed: $($Arguments -join ' ')" }
}

& $adb start-server | Out-Host
if ($LASTEXITCODE -ne 0) { throw "adb start-server failed." }

$existing = @(Get-OnlineEmulators)
$script:serial = $null
$script:ownsEmulator = $false
$script:emulatorProcess = $null
$script:emulatorStdout = $null
$script:emulatorStderr = $null

if ($existing.Count -gt 1) {
    throw "More than one online Android emulator is present ($($existing -join ', ')). Runtime CI refuses to choose implicitly."
}

if ($existing.Count -eq 1) {
    $script:serial = $existing[0]
    Write-Host "Reusing existing Android emulator without resetting it: $script:serial"
} else {
    $avds = @(& $emulator -list-avds | Where-Object { $_ -and $_.Trim() })
    if ($LASTEXITCODE -ne 0 -or $avds.Count -eq 0) { throw "No local Android AVD is available for runtime instrumentation." }
    $avd = $avds[0].Trim()
    $script:emulatorStdout = Join-Path $env:RUNNER_TEMP "android-runtime-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.stdout.log"
    $script:emulatorStderr = Join-Path $env:RUNNER_TEMP "android-runtime-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.stderr.log"
    Remove-Item -LiteralPath $script:emulatorStdout,$script:emulatorStderr -Force -ErrorAction SilentlyContinue
    Write-Host "Starting isolated read-only Android AVD: $avd"
    $script:emulatorProcess = Start-Process -FilePath $emulator -ArgumentList @(
        '-avd', $avd,
        '-read-only',
        '-no-window',
        '-no-snapshot',
        '-noaudio',
        '-no-boot-anim',
        '-no-metrics',
        '-gpu', 'swiftshader_indirect'
    ) -RedirectStandardOutput $script:emulatorStdout -RedirectStandardError $script:emulatorStderr -PassThru
    $script:ownsEmulator = $true

    $deadline = (Get-Date).AddMinutes(4)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        $script:emulatorProcess.Refresh()
        if ($script:emulatorProcess.HasExited) {
            Write-EmulatorDiagnostics
            throw "The isolated Android emulator exited before becoming available."
        }
        $candidate = @(Get-OnlineEmulators | Select-Object -First 1)
        if ($candidate.Count -eq 0) { continue }
        $script:serial = $candidate[0]
        $booted = (& $adb -s $script:serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
        if ($booted -eq '1') { break }
    }
    if (-not $script:serial) {
        Write-EmulatorDiagnostics
        throw "The isolated Android emulator did not become available within four minutes."
    }
}

$deadline = (Get-Date).AddMinutes(4)
while ((Get-Date) -lt $deadline) {
    $booted = (& $adb -s $script:serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
    if ($booted -eq '1') { break }
    Start-Sleep -Seconds 2
}
$booted = (& $adb -s $script:serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
if ($booted -ne '1') {
    Write-EmulatorDiagnostics
    throw "Android emulator did not finish booting within four minutes."
}

Write-Host "Android runtime instrumentation device: $script:serial"
$previousSerial = $env:ANDROID_SERIAL
$env:ANDROID_SERIAL = $script:serial

Push-Location $androidRoot
try {
    # Phase16HUpgradeTest is intentionally stateful: its dedicated update gate seeds
    # versionCode 1 data, replaces the APK in-place, then verifies migration/retention.
    # Running that class inside the generic suite makes verifyPreservedAndMigrated
    # fail without the required real APK-replacement setup.
    Invoke-Gradle @(
        'connectedChecksAndroidTest',
        '-Pandroid.testInstrumentationRunnerArguments.notClass=gr.mastixa.manager.Phase16HUpgradeTest',
        '--console=plain'
    )
    Write-Host "Android runtime instrumentation passed."
}
finally {
    Pop-Location
    if ($null -eq $previousSerial) { Remove-Item Env:ANDROID_SERIAL -ErrorAction SilentlyContinue } else { $env:ANDROID_SERIAL = $previousSerial }
    if ($script:ownsEmulator -and $script:serial) {
        & $adb -s $script:serial emu kill | Out-Null
    }
}
