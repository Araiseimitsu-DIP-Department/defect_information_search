from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QImage


def main() -> int:
    root_dir = Path(__file__).resolve().parents[1]
    source_path = root_dir / "docs" / "icon.png"
    output_path = root_dir / "build" / "app_icon.ico"

    if not source_path.exists():
        print(f"icon source not found: {source_path}", file=sys.stderr)
        return 1

    image = QImage(str(source_path))
    if image.isNull():
        print(f"failed to load icon: {source_path}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(output_path), "ICO"):
        print(f"failed to save ico: {output_path}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
