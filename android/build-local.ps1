param([switch]$Test)
$ErrorActionPreference = 'Stop'
if (-not $env:JAVA_HOME) { throw 'Set JAVA_HOME to a JDK 17 or 21 installation.' }
if (-not $env:ANDROID_HOME -and -not (Test-Path "$PSScriptRoot/local.properties")) {
    throw 'Set ANDROID_HOME to the Android SDK, or configure sdk.dir in local.properties.'
}
Push-Location $PSScriptRoot
try {
    if ($Test) { & ./gradlew.bat assembleDebug connectedChecksAndroidTest --console=plain }
    else { & ./gradlew.bat assembleDebug --console=plain }
    if ($LASTEXITCODE -ne 0) { throw 'Android build failed.' }
} finally { Pop-Location }
