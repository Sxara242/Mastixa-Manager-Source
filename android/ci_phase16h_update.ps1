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
    Write-Host "=== Emulator diagnostics ==="
    Write-Host "adb devices -l:"
    & $adb devices -l | Out-Host
    if (Test-Path -LiteralPath $script:emulatorStdout) {
        Write-Host "--- emulator stdout ---"
        Get-Content -LiteralPath $script:emulatorStdout -ErrorAction SilentlyContinue | Out-Host
    }
    if (Test-Path -LiteralPath $script:emulatorStderr) {
        Write-Host "--- emulator stderr ---"
        Get-Content -LiteralPath $script:emulatorStderr -ErrorAction SilentlyContinue | Out-Host
    }
    Write-Host "=== End emulator diagnostics ==="
}

function Invoke-Adb {
    param([string[]]$Arguments)
    & $adb -s $script:serial @Arguments
    if ($LASTEXITCODE -ne 0) { throw "adb failed: $($Arguments -join ' ')" }
}

function Invoke-Gradle {
    param([string[]]$Arguments)
    & .\gradlew.bat @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Gradle failed: $($Arguments -join ' ')" }
}

function Invoke-OneTest {
    param([string]$Selector)
    $lines = & $adb -s $script:serial shell am instrument -w -r -e class $Selector `
        gr.mastixa.manager.checks.test/androidx.test.runner.AndroidJUnitRunner 2>&1
    $exitCode = $LASTEXITCODE
    $output = ($lines | Out-String)
    Write-Host $output
    if ($exitCode -ne 0 -or $output -notmatch 'OK \(1 test\)') {
        throw "Instrumentation test failed: $Selector"
    }
}

& $adb start-server | Out-Host
if ($LASTEXITCODE -ne 0) { throw "adb start-server failed." }

Write-Host "Android emulator version:"
& $emulator -version 2>&1 | Select-Object -First 8 | Out-Host
$before = @(Get-OnlineEmulators)
Write-Host "Online emulator serials before launch: $($before -join ', ')"
$avds = @(& $emulator -list-avds | Where-Object { $_ -and $_.Trim() })
if ($LASTEXITCODE -ne 0 -or $avds.Count -eq 0) { throw "No local Android AVD is available for the Phase 16H gate." }
$avd = $avds[0].Trim()
$script:emulatorStdout = Join-Path $env:RUNNER_TEMP "phase16h-emulator-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.stdout.log"
$script:emulatorStderr = Join-Path $env:RUNNER_TEMP "phase16h-emulator-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.stderr.log"
Remove-Item -LiteralPath $script:emulatorStdout,$script:emulatorStderr -Force -ErrorAction SilentlyContinue
Write-Host "Starting isolated read-only AVD: $avd"
$emulatorProcess = Start-Process -FilePath $emulator -ArgumentList @(
    '-avd', $avd,
    '-read-only',
    '-no-window',
    '-no-snapshot',
    '-noaudio',
    '-no-boot-anim',
    '-no-metrics',
    '-gpu', 'swiftshader_indirect',
    '-verbose'
) -RedirectStandardOutput $script:emulatorStdout -RedirectStandardError $script:emulatorStderr -PassThru
Write-Host "Emulator launcher PID: $($emulatorProcess.Id)"

$script:serial = $null
$deadline = (Get-Date).AddMinutes(4)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    $emulatorProcess.Refresh()
    if ($emulatorProcess.HasExited) {
        Write-Host "Emulator launcher exited early with code $($emulatorProcess.ExitCode)."
        Write-EmulatorDiagnostics
        throw "The isolated Android emulator exited before becoming available."
    }
    $candidate = @(Get-OnlineEmulators | Where-Object { $before -notcontains $_ } | Select-Object -First 1)
    if ($candidate.Count -eq 0) { continue }
    $script:serial = $candidate[0]
    $booted = (& $adb -s $script:serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
    if ($booted -eq '1') { break }
}
if (-not $script:serial) {
    Write-EmulatorDiagnostics
    if (-not $emulatorProcess.HasExited) { Stop-Process -Id $emulatorProcess.Id -Force -ErrorAction SilentlyContinue }
    throw "The isolated Android emulator did not become available within four minutes."
}
$booted = (& $adb -s $script:serial shell getprop sys.boot_completed 2>$null | Out-String).Trim()
if ($booted -ne '1') {
    Write-EmulatorDiagnostics
    & $adb -s $script:serial emu kill | Out-Null
    throw "The isolated Android emulator did not finish booting within four minutes."
}
Write-Host "Phase 16H emulator ready: $script:serial"

Push-Location $androidRoot
try {
    Write-Host "=== Build and install baseline versionCode 1 ==="
    Invoke-Gradle @(
        'assembleDebug', 'assembleChecks', 'assembleChecksAndroidTest',
        '-PmastixaVersionCode=1', '-PmastixaVersionName=0.39.0-upgrade-fixture', '--console=plain'
    )
    Invoke-Adb @('install', '-r', '-d', 'app\build\outputs\apk\debug\app-debug.apk')
    Invoke-Adb @('install', '-r', '-d', 'app\build\outputs\apk\checks\app-checks.apk')
    Invoke-Adb @('install', '-r', '-d', 'app\build\outputs\apk\androidTest\checks\app-checks-androidTest.apk')
    Invoke-OneTest 'gr.mastixa.manager.Phase16HUpgradeTest#seedLegacyState'

    Write-Host "=== Update both APKs in place; no uninstall, pm clear, or emulator reset ==="
    Invoke-Gradle @('assembleDebug', 'assembleChecks', 'assembleChecksAndroidTest', '--console=plain')
    Invoke-Adb @('install', '-r', 'app\build\outputs\apk\debug\app-debug.apk')
    Invoke-Adb @('install', '-r', 'app\build\outputs\apk\checks\app-checks.apk')
    Invoke-Adb @('install', '-r', 'app\build\outputs\apk\androidTest\checks\app-checks-androidTest.apk')

    $mainPackage = (& $adb -s $script:serial shell dumpsys package gr.mastixa.manager | Out-String)
    $checksPackage = (& $adb -s $script:serial shell dumpsys package gr.mastixa.manager.checks | Out-String)
    if ($mainPackage -notmatch 'versionCode=2\b' -or $mainPackage -notmatch 'versionName=0\.40\.0-alpha\.1') {
        throw "Main APK did not update to 0.40.0-alpha.1 / versionCode 2."
    }
    if ($checksPackage -notmatch 'versionCode=2\b' -or $checksPackage -notmatch 'versionName=0\.40\.0-alpha\.1') {
        throw "Checks APK did not update to 0.40.0-alpha.1 / versionCode 2."
    }

    Invoke-OneTest 'gr.mastixa.manager.Phase16HUpgradeTest#verifyPreservedAndMigrated'
    Invoke-OneTest 'gr.mastixa.manager.Phase16HUpgradeTest#storageAccessUsesSafWithoutBroadStoragePermissions'
    Invoke-OneTest 'gr.mastixa.manager.ExportFailureUiTest#unavailableDocumentPickerDoesNotCrashOrRetainPreparedFile'
    Write-Host "Phase 16H Android update verification passed."
}
finally {
    Pop-Location
    if ($script:serial) {
        & $adb -s $script:serial emu kill | Out-Null
    }
}
