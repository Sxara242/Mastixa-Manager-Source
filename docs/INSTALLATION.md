# Installation and local data

Windows x64 is the current release target. No public rc.2 installer is approved;
the older rc.1 candidate is historical and lacks subsequent fixes.
Android remains in development. Download binary releases only after the
[release status](RELEASE_STATUS.md) and published checksums explicitly qualify them.

For Windows source development, install Python 3.14 and create a virtual
environment. The first install downloads dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements-windows-rc.txt
.\.venv\Scripts\python.exe main.py
```

Normal application data lives under `%LOCALAPPDATA%\MastixaManager`, separate
from program files. Set `MASTIXA_DATA_HOME` to a new disposable directory before
development launches. Keep databases, backups and profile exports outside the
source tree. Back up real data before installation, upgrade or uninstall.

The qualified Windows installer route requires an independently installed
official Microsoft x64 Visual C++ Redistributable **>=14.51.36247.0**.
Mastixa bundles neither Microsoft CRT DLLs nor the redistributable installer;
the prerequisite fails closed. Source CI does not establish binary readiness.

For Android install JDK 21 and Android SDK platform 36, set `JAVA_HOME` and
`ANDROID_HOME`, and run from `android/`:

```powershell
.\gradlew.bat --no-daemon testDebugUnitTest lintDebug assembleDebug assembleChecksAndroidTest
```

On Linux use `bash ./gradlew` with the same tasks. Debug APKs are development
outputs. `connectedChecksAndroidTest` requires an emulator/device and uses a
separate `.checks` application. JVM unit tasks presently have no test sources;
they do not substitute for instrumentation. Do not provide production signing
keys for CI. See [Android documentation](../android/README.md).
