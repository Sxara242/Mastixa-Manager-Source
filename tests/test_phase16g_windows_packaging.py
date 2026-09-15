from __future__ import annotations

from pathlib import Path
import re
import unittest

from app.runtime_paths import resolve_base_dir


ROOT = Path(__file__).resolve().parents[1]


class Phase16GWindowsPackagingTests(unittest.TestCase):
    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_release_versions_are_consistent(self) -> None:
        readme = self._read("README.md")
        iss = self._read("installer/MastixaManager.iss")
        version_info = self._read("packaging/version_info.txt")

        readme_match = re.search(r"^# Mastixa Manager v([^\s]+)", readme, re.MULTILINE)
        iss_match = re.search(r'^#define MyAppVersion "([^"]+)"', iss, re.MULTILINE)
        file_match = re.search(r"StringStruct\('FileVersion', '([^']+)'\)", version_info)
        product_match = re.search(r"StringStruct\('ProductVersion', '([^']+)'\)", version_info)

        for match in (readme_match, iss_match, file_match, product_match):
            self.assertIsNotNone(match)

        versions = {
            readme_match.group(1),
            iss_match.group(1),
            file_match.group(1),
            product_match.group(1),
        }
        self.assertEqual(1, len(versions), f"Release versions drifted: {sorted(versions)}")

    def test_installer_upgrade_contract_preserves_external_user_data(self) -> None:
        iss = self._read("installer/MastixaManager.iss")

        self.assertIn("AppId={{B9B946A2-8711-4B35-9BCB-B40210E67357}", iss)
        self.assertIn("PrivilegesRequired=lowest", iss)
        self.assertIn("DefaultDirName={%LOCALAPPDATA}\\Programs\\Mastixa Manager", iss)
        self.assertNotIn("MastixaManager\\data", iss)
        self.assertNotIn("MastixaManager\\backups", iss)

        data_dir = resolve_base_dir(
            frozen=True,
            environ={"LOCALAPPDATA": "C:/Users/test/AppData/Local"},
        )
        install_dir = Path("C:/Users/test/AppData/Local/Programs/Mastixa Manager").resolve()
        self.assertEqual(
            Path("C:/Users/test/AppData/Local/MastixaManager").resolve(),
            data_dir,
        )
        self.assertNotEqual(install_dir, data_dir)
        self.assertNotIn(install_dir, data_dir.parents)

    def test_bundle_contract_includes_runtime_assets_and_excludes_private_data(self) -> None:
        spec = self._read("packaging/MastixaManager.spec")
        build = self._read("packaging/build_release.ps1")

        self.assertIn('"app/assets"', spec)
        self.assertIn('"app/locales"', spec)
        self.assertNotIn('"data/mastixa_manager.db"', spec)
        self.assertNotIn('"backups"', spec)

        self.assertIn('"_internal\\data"', build)
        self.assertIn('Filter "*.db"', build)
        self.assertIn("Private application data unexpectedly entered the build", build)
        self.assertIn("Unexpected SQLite database files entered the release bundle", build)

    def test_database_privacy_gate_allows_only_pyproj_dependency_database(self) -> None:
        build = self._read("packaging/build_release.ps1")
        workflow = self._read(".github/workflows/windows-release-gate.yml")

        self.assertIn('$databaseFile.Name -ieq "proj.db"', build)
        self.assertIn('$relativePath -match "(^|/)pyproj(/|$)"', build)
        self.assertIn("Allowed dependency database", build)
        self.assertIn("$unexpectedDatabaseFiles", build)
        self.assertNotIn("SQLite database files unexpectedly entered the release bundle", build)
        self.assertIn("p.name.lower() == 'proj.db'", workflow)
        self.assertIn("'pyproj' in [part.lower() for part in p.parts]", workflow)

    def test_release_builder_is_windows_powershell_compatible(self) -> None:
        build = self._read("packaging/build_release.ps1")

        self.assertIn("function Get-BundleRelativePath", build)
        self.assertIn("[System.StringComparison]::OrdinalIgnoreCase", build)
        self.assertNotIn("[System.IO.Path]::GetRelativePath", build)

    def test_release_gate_bootstraps_pinned_inno_setup_for_current_user(self) -> None:
        build = self._read("packaging/build_release.ps1")
        workflow = self._read(".github/workflows/windows-release-gate.yml")

        self.assertIn('Programs\\Inno Setup 6\\ISCC.exe', build)
        self.assertIn("runs-on: [self-hosted, Windows, X64]", workflow)
        self.assertIn("Ensure Inno Setup 6 compiler", workflow)
        self.assertIn("JRSoftware.InnoSetup", workflow)
        self.assertIn("--version 6.7.3", workflow)
        self.assertIn("--scope user", workflow)
        self.assertIn("--disable-interactivity", workflow)
        self.assertIn('%LOCALAPPDATA%\\Programs\\Inno Setup 6\\ISCC.exe', workflow)

    def test_release_output_is_isolated_and_retries_transient_windows_locks(self) -> None:
        build = self._read("packaging/build_release.ps1")
        ci_build = self._read("packaging/ci_windows_release.ps1")
        workflow = self._read(".github/workflows/windows-release-gate.yml")

        self.assertIn('[string]$InstallerOutputDir = ""', build)
        self.assertIn("[int]$InstallerBuildAttempts = 3", build)
        self.assertIn('$outputArg = "/O$installerOutput"', build)
        self.assertIn("for ($attempt = 1; $attempt -le $InstallerBuildAttempts; $attempt++)", build)
        self.assertIn("Retrying in $delaySeconds seconds", build)
        self.assertIn('$outputDir = Join-Path $env:RUNNER_TEMP', ci_build)
        self.assertIn('$env:GITHUB_RUN_ID', ci_build)
        self.assertIn('$env:GITHUB_RUN_ATTEMPT', ci_build)
        self.assertIn("-InstallerOutputDir $outputDir", ci_build)
        self.assertIn("-InstallerBuildAttempts 3", ci_build)
        self.assertIn("packaging\\ci_windows_release.ps1", workflow)
        self.assertNotIn(
            'if not exist "dist\\installer\\MastixaManager-0.40.0-alpha.1-Setup.exe"',
            workflow,
        )

    def test_release_gate_uses_tracked_non_invasive_lock_diagnostics(self) -> None:
        ci_build = self._read("packaging/ci_windows_release.ps1")
        workflow = self._read(".github/workflows/windows-release-gate.yml")

        self.assertIn("download.sysinternals.com/files/Handle.zip", ci_build)
        self.assertIn("Get-AuthenticodeSignature", ci_build)
        self.assertIn('-notmatch "Microsoft"', ci_build)
        self.assertIn("Start-Job", ci_build)
        self.assertIn("Observed installer file locks", ci_build)
        self.assertIn("-ExecutionPolicy Bypass -File packaging\\ci_windows_release.ps1", workflow)
        self.assertNotIn("shell: powershell", workflow)
        self.assertNotIn("Stop-Process", ci_build)
        self.assertNotIn("Add-MpPreference", ci_build)
        self.assertNotIn("Set-MpPreference", ci_build)

    def test_release_gate_publishes_short_lived_installer_artifact(self) -> None:
        workflow = self._read(".github/workflows/windows-release-gate.yml")

        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("MastixaManager-0.40.0-alpha.1-Windows", workflow)
        self.assertIn("retention-days: 7", workflow)
        self.assertIn("${{ runner.temp }}", workflow)
        self.assertIn("${{ github.run_id }}", workflow)
        self.assertIn("${{ github.run_attempt }}", workflow)

    def test_release_builder_is_ci_usable_and_hashes_dynamic_version_installer(self) -> None:
        build = self._read("packaging/build_release.ps1")
        requirements = self._read("requirements-build.txt").strip()

        self.assertIn('[string]$PythonPath = ""', build)
        self.assertIn("-PythonPath <python.exe>", build)
        self.assertIn("MyAppVersion", build)
        self.assertIn('"MastixaManager-$version-Setup.exe"', build)
        self.assertIn("Get-FileHash -Algorithm SHA256", build)
        self.assertEqual("PyInstaller==6.22.2", requirements)


if __name__ == "__main__":
    unittest.main()
