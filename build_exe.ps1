param(
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

$AppName = [string]::Concat([char[]](0x4E0D, 0x5177, 0x5408, 0x60C5, 0x5831, 0x691C, 0x7D22))
$Root = (Resolve-Path ".").Path
$BuildDir = Join-Path $Root "build"
$DocsDir = Join-Path $Root "docs"
$SourceIconName = [string]::Concat([char[]](0x5DE5,0x696D,0x691C,0x67FB,0x3068,0x30A8,0x30E9,0x30FC,0x691C,0x51FA,0x30A2,0x30A4,0x30B3,0x30F3,0x002E,0x0070,0x006E,0x0067))
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

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

if (Test-Path $BuildDir) {
    Remove-Item $BuildDir -Recurse -Force
}

$pngCandidates = Get-ChildItem $DocsDir -File | Where-Object { $_.Name -eq $SourceIconName }
if (-not $pngCandidates) {
    throw "Icon source PNG not found in docs."
}

New-AppIcon -SourcePath $pngCandidates[0].FullName -DestinationPath $RuntimeIconPath

if (-not (Test-Path ".\.env")) {
    throw "Missing .env in repository root."
}

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
    "--add-data", ".env;.",
    "--add-data", "src\defect_information_search\webview\assets;defect_information_search\webview\assets",
    "main.py"
)

& $PythonExe @pyInstallerArgs

if (Test-Path ".\$AppName.spec") {
    Remove-Item ".\$AppName.spec" -Force
}

if (Test-Path $BuildDir) {
    Remove-Item $BuildDir -Recurse -Force
}
