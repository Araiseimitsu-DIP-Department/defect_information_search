param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [ValidateSet("postgres", "access")]
    [string]$Backend = "postgres"
)

$ErrorActionPreference = "Stop"
$AppName = [string]::Concat([char[]](0x4E0D, 0x5177, 0x5408, 0x60C5, 0x5831, 0x691C, 0x7D22))
$Root = (Resolve-Path ".").Path
if ($Root -ne $PSScriptRoot) {
    throw "Run this script from the repository root."
}
$BuildDir = Join-Path $Root "build"
$DistDir = Join-Path $Root "dist"
$DocsDir = Join-Path $Root "docs"
$SourceIconName = "app_icon.png"
$RuntimeIconName = "app_icon.ico"
$RuntimeIconPath = Join-Path $BuildDir $RuntimeIconName

function New-AppIcon {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    Add-Type -AssemblyName System.Drawing

    if (-not (Test-Path $SourcePath)) {
        throw "Icon source not found: $SourcePath"
    }

    $sourceImage = [System.Drawing.Image]::FromFile($SourcePath)
    try {
        $sizes = @(16, 32, 48, 64, 128, 256)
        $images = New-Object System.Collections.Generic.List[byte[]]
        $entries = New-Object System.Collections.Generic.List[object]

        foreach ($size in $sizes) {
            $bitmap = New-Object System.Drawing.Bitmap $size, $size
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $memoryStream = New-Object System.IO.MemoryStream
            try {
                $graphics.Clear([System.Drawing.Color]::Transparent)
                $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.DrawImage($sourceImage, 0, 0, $size, $size)
                $bitmap.Save($memoryStream, [System.Drawing.Imaging.ImageFormat]::Png)

                $blob = $memoryStream.ToArray()
                [void]$images.Add($blob)
                [void]$entries.Add([pscustomobject]@{
                    Width = if ($size -eq 256) { 0 } else { $size }
                    Height = if ($size -eq 256) { 0 } else { $size }
                    Length = $blob.Length
                })
            }
            finally {
                $memoryStream.Dispose()
                $graphics.Dispose()
                $bitmap.Dispose()
            }
        }

        $destinationDirectory = Split-Path -Parent $DestinationPath
        if ($destinationDirectory -and -not (Test-Path $destinationDirectory)) {
            New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
        }

        $stream = [System.IO.File]::Open($DestinationPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
        $writer = New-Object System.IO.BinaryWriter($stream)
        try {
            $writer.Write([UInt16]0)
            $writer.Write([UInt16]1)
            $writer.Write([UInt16]$images.Count)

            $offset = 6 + (16 * $images.Count)
            for ($index = 0; $index -lt $images.Count; $index++) {
                $entry = $entries[$index]
                $writer.Write([byte]$entry.Width)
                $writer.Write([byte]$entry.Height)
                $writer.Write([byte]0)
                $writer.Write([byte]0)
                $writer.Write([UInt16]1)
                $writer.Write([UInt16]32)
                $writer.Write([UInt32]$entry.Length)
                $writer.Write([UInt32]$offset)
                $offset += $entry.Length
            }

            foreach ($blob in $images) {
                $writer.Write($blob)
            }
        }
        finally {
            $writer.Dispose()
            $stream.Dispose()
        }
    }
    finally {
        $sourceImage.Dispose()
    }
}

if (Test-Path -LiteralPath $DistDir) {
    Remove-Item -LiteralPath $DistDir -Recurse -Force
}

if (Test-Path $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

$pngCandidates = Get-ChildItem $DocsDir -File | Where-Object { $_.Name -eq $SourceIconName }
if (-not $pngCandidates) {
    throw "Icon source PNG not found in docs."
}

New-AppIcon -SourcePath $pngCandidates[0].FullName -DestinationPath $RuntimeIconPath

if (-not (Test-Path ".\.env")) {
    throw "Missing .env in repository root."
}

$BundledEnv = Join-Path $BuildDir ".env"
& $PythonExe tools\build_support.py prepare .env --backend $Backend --destination $BundledEnv
if ($LASTEXITCODE -ne 0) { throw "Build settings preparation failed." }

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", $AppName,
    "--paths", "src",
    "--runtime-hook", "tools\pyi_rth_fix_six.py",
    "--icon", $RuntimeIconPath,
    "--collect-all", "webview",
    "--hidden-import", "webview.platforms.edgechromium",
    "--hidden-import", "webview.platforms.winforms",
    "--hidden-import", "webview.platforms.win32",
    "--exclude-module", "PySide6",
    "--exclude-module", "PyQt5",
    "--exclude-module", "PyQt6",
    "--exclude-module", "qtpy",
    "--exclude-module", "PyQt6.QtWebEngineWidgets",
    "--exclude-module", "PyQt6.QtWebEngineCore",
    "--exclude-module", "PyQt6.QtWebEngineQuick",
    "--exclude-module", "PySide6.QtWebEngineWidgets",
    "--exclude-module", "PySide6.QtWebEngineCore",
    "--exclude-module", "PySide6.QtWebEngineQuick",
    "--add-data", "$RuntimeIconPath;.",
    "--add-data", "$BundledEnv;.",
    "--add-data", "$(Join-Path $BuildDir 'build_backend.txt');.",
    "--add-data", "src\defect_information_search\webview\assets;defect_information_search\webview\assets"
)

if ($Backend -eq "postgres") {
    foreach ($module in @("pyodbc", "pypyodbc", "defect_information_search.infrastructure.access", "defect_information_search.infrastructure.access_gateway")) {
        $pyInstallerArgs += @("--exclude-module", $module)
    }
}
$pyInstallerArgs += "main.py"
& $PythonExe @pyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

& $PythonExe tools\build_support.py verify (Join-Path $DistDir "$AppName.exe") --backend $Backend
if ($LASTEXITCODE -ne 0) { throw "Build archive verification failed." }

if (Test-Path ".\$AppName.spec") {
    Remove-Item ".\$AppName.spec" -Force
}

if (Test-Path $BuildDir) {
    Remove-Item $BuildDir -Recurse -Force
}
