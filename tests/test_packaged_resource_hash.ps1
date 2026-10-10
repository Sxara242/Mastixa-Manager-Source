# Synthetic resource preflight only: never launch an executable or installer.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $repo 'packaging\smoke_test_packaged.ps1'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors)
if ($errors.Count -ne 0) { throw 'Smoke script did not parse.' }
$functions = @($ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Get-ResourceSha256'
}, $true))
if ($functions.Count -ne 1) { throw 'Expected exactly one SHA-256 helper.' }
. ([scriptblock]::Create($functions[0].Extent.Text))
# Extract the actual resource loop, stopping before isolation/process setup.
$loops = @($ast.EndBlock.Statements | Where-Object {
    $_ -is [System.Management.Automation.Language.ForEachStatementAst] -and
    $_.Variable.VariablePath.UserPath -eq 'resource'
})
if ($loops.Count -ne 1) { throw 'Expected exactly one resource validation loop.' }
$validate = [scriptblock]::Create($loops[0].Extent.Text)
function Assert-Fails {
    param([scriptblock]$Action, [string]$Message)
    $failed = $false
    try { & $Action | Out-Null } catch {
        if ($_.Exception.Message -notlike $Message) { throw }
        $failed = $true
    }
    if (-not $failed) { throw "Expected failure: $Message" }
}
# A shadow command proves preflight no longer depends on that cmdlet.
function Get-FileHash { throw 'Forbidden Get-FileHash dependency.' }
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('mastixa-hash-' + [guid]::NewGuid().ToString('N'))
$repoRoot = Join-Path $fixture 'source'
$bundle = Join-Path $fixture 'bundle'
try {
    foreach ($resource in @('assets', 'locales')) {
        foreach ($base in @((Join-Path $repoRoot "app\$resource"), (Join-Path $bundle "_internal\app\$resource"))) {
            [System.IO.Directory]::CreateDirectory((Join-Path $base 'nested')) | Out-Null
            [System.IO.File]::WriteAllBytes((Join-Path $base 'nested\literal[1].bin'), [byte[]](0, 1, 254, 255))
        }
    }
    $source = Join-Path $repoRoot 'app\assets\nested\literal[1].bin'
    $packaged = Join-Path $bundle '_internal\app\assets\nested\literal[1].bin'
    $known = Join-Path $fixture 'known.bin'
    [System.IO.File]::WriteAllBytes($known, [byte[]](97, 98, 99))
    if ((Get-ResourceSha256 -LiteralPath $known) -cne 'BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD') {
        throw 'SHA-256 known vector failed.'
    }
    & $validate
    # Inject a ComputeHash failure into a test-only copy of the actual helper.
    # Production retains its .NET SHA256 factory with no injection hook.
    $script:hasherDisposed = $false
    function New-FailingHasher {
        $hasher = New-Object PSObject
        $hasher | Add-Member ScriptMethod ComputeHash { param($stream) throw 'Synthetic hash error' }
        $hasher | Add-Member ScriptMethod Dispose { $script:hasherDisposed = $true }
        return $hasher
    }
    $failingHelper = $functions[0].Extent.Text.Replace('[System.Security.Cryptography.SHA256]::Create()', '(New-FailingHasher)')
    . ([scriptblock]::Create($failingHelper))
    Assert-Fails { & $validate } '*Synthetic hash error*'
    if (-not $script:hasherDisposed) { throw 'Failed hasher was not disposed.' }
    . ([scriptblock]::Create($functions[0].Extent.Text))
    & $validate
    [System.IO.File]::WriteAllBytes($packaged, [byte[]](0, 1, 254, 0))
    Assert-Fails { & $validate } '*Packaged resource differs*'
    [System.IO.File]::Delete($packaged)
    Assert-Fails { & $validate } '*Missing packaged resource*'
    Assert-Fails { Get-ResourceSha256 -LiteralPath $packaged } '*'
    [System.IO.File]::WriteAllBytes($packaged, [System.IO.File]::ReadAllBytes($source))
    # Windows FileShare.None makes the resource genuinely unreadable.
    $lock = [System.IO.File]::Open($packaged, 'Open', 'ReadWrite', 'None')
    try { Assert-Fails { & $validate } '*' } finally { $lock.Dispose() }
    $lock = [System.IO.File]::Open($source, 'Open', 'ReadWrite', 'None')
    try { Assert-Fails { & $validate } '*' } finally { $lock.Dispose() }
    & $validate
    # Successful and failed paths must release handles, including the source
    # handle opened before SHA256.Create/ComputeHash runs.
    foreach ($path in @($source, $packaged, $known)) {
        $handle = [System.IO.File]::Open($path, 'Open', 'ReadWrite', 'None')
        $handle.Dispose()
    }
    Write-Host 'PASS: SHA-256 vector, matches, mismatch, missing, read/hash errors, handle disposal.'
}
finally {
    # Only this test's newly created synthetic GUID directory is removed.
    if ([System.IO.Directory]::Exists($fixture)) { [System.IO.Directory]::Delete($fixture, $true) }
}
