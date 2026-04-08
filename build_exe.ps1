param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

& $PythonExe .\tools\prepare_icon.py
if ($LASTEXITCODE -ne 0) {
    throw "アイコンファイルの準備に失敗しました。"
}

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "defect_information_search" `
    --paths "src" `
    --icon "build\app_icon.ico" `
    --add-data "docs\icon.png;docs" `
    --add-data "src\defect_information_search\ui_kit\assets;defect_information_search\ui_kit\assets" `
    main.py
