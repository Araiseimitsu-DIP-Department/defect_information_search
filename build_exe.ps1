param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

$AppName = [string]::Concat([char[]](0x4E0D, 0x5177, 0x5408, 0x60C5, 0x5831, 0x691C, 0x7D22))

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

if (Test-Path ".\build\$AppName") {
    Remove-Item ".\build\$AppName" -Recurse -Force
}

if (Test-Path ".\build\defect_information_search") {
    Remove-Item ".\build\defect_information_search" -Recurse -Force
}

& $PythonExe .\tools\prepare_icon.py
if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare icon."
}

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", $AppName,
    "--paths", "src",
    "--runtime-hook", "tools\\pyi_rth_fix_six.py",
    "--icon", "build\app_icon.ico",
    "--add-data", "docs\icon.png;docs",
    "--add-data", "src\defect_information_search\ui_kit\assets;defect_information_search\ui_kit\assets",
    "main.py"
)

if (Test-Path ".\.env") {
    $pyInstallerArgs += @("--add-data", ".env;.")
}

& $PythonExe @pyInstallerArgs

if (Test-Path ".\$AppName.spec") {
    Remove-Item ".\$AppName.spec" -Force
}
