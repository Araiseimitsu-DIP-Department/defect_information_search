from __future__ import annotations

import sys
from pathlib import Path

# パッケージ未インストール環境でも config を参照できるようにする
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from defect_information_search.config import APP_ICON_RUNTIME_FILENAME, APP_ICON_SOURCE_FILENAME
from PySide6.QtGui import QImage


def main() -> int:
    root_dir = _ROOT
    source_path = root_dir / "docs" / APP_ICON_SOURCE_FILENAME
    ico_path = root_dir / "build" / "app_icon.ico"
    runtime_png_path = root_dir / "build" / APP_ICON_RUNTIME_FILENAME

    if not source_path.exists():
        print(f"icon source not found: {source_path}", file=sys.stderr)
        return 1

    image = QImage(str(source_path))
    if image.isNull():
        print(f"failed to load icon: {source_path}", file=sys.stderr)
        return 1

    ico_path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(ico_path), "ICO"):
        print(f"failed to save ico: {ico_path}", file=sys.stderr)
        return 1
    # PyInstaller へ日本語パスを渡さないよう、同梱用 PNG は ASCII 名で build に出力する
    if not image.save(str(runtime_png_path), "PNG"):
        print(f"failed to save png: {runtime_png_path}", file=sys.stderr)
        return 1

    print(ico_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
