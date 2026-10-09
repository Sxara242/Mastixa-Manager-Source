// B2: recipient installs the official x64 VC Redist independently.
// No runtime installer/DLL is embedded, downloaded or invoked by Mastixa.
// Microsoft servicing owns the prerequisite. Fail closed before app installation.
const
  VcRuntimeKey = 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';

function VcVersionAtLeast(Major, Minor, Build, Revision: Cardinal): Boolean;
begin
  Result := (Major > 14) or
    ((Major = 14) and ((Minor > 51) or
      ((Minor = 51) and ((Build > 36247) or
        ((Build = 36247) and (Revision >= 0))))));
end;

function VcRuntimeVersionInView(RootKey: Integer): Boolean;
var
  Installed, Major, Minor, Build, Revision: Cardinal;
begin
  Result := RegQueryDWordValue(RootKey, VcRuntimeKey, 'Installed', Installed) and
    (Installed = 1) and
    RegQueryDWordValue(RootKey, VcRuntimeKey, 'Major', Major) and
    RegQueryDWordValue(RootKey, VcRuntimeKey, 'Minor', Minor) and
    RegQueryDWordValue(RootKey, VcRuntimeKey, 'Bld', Build) and
    RegQueryDWordValue(RootKey, VcRuntimeKey, 'Rbld', Revision);
  if Result then
    Result := VcVersionAtLeast(Major, Minor, Build, Revision);
end;

function VcCanonicalFileReady(const Name: String): Boolean;
var
  VersionMS, VersionLS: Cardinal;
begin
  Result := GetVersionNumbers(ExpandConstant('{sys}\') + Name, VersionMS, VersionLS);
  if Result then
    Result := VcVersionAtLeast(VersionMS shr 16, VersionMS and $FFFF,
      VersionLS shr 16, VersionLS and $FFFF);
end;

function VcRedistPrerequisiteReady: Boolean;
begin
  Result := IsWin64 and
    (VcRuntimeVersionInView(HKLM64) or VcRuntimeVersionInView(HKLM32)) and
    VcCanonicalFileReady('msvcp140.dll') and
    VcCanonicalFileReady('msvcp140_1.dll') and
    VcCanonicalFileReady('msvcp140_2.dll') and
    VcCanonicalFileReady('vcruntime140.dll') and
    VcCanonicalFileReady('vcruntime140_1.dll');
end;

function VcRedistPrerequisiteMessage: String;
begin
  Result := 'Install the official Microsoft Visual C++ v14 x64 Redistributable ' +
    '(version 14.51.36247.0 or newer), then run Mastixa Setup again.' + #13#10 +
    'Official Microsoft page: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist' + #13#10 +
    'Mastixa does not download or install this prerequisite automatically.';
end;
