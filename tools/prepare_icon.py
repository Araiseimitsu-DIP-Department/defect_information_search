from __future__ import annotations

import struct
import sys
from pathlib import Path

# パッケージ未インストール環境でも config を参照できるようにする
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage

from defect_information_search.config import APP_ICON_RUNTIME_FILENAME, APP_ICON_SOURCE_FILENAME


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
    if not _write_multi_size_ico(image, ico_path):
        print(f"failed to save ico: {ico_path}", file=sys.stderr)
        return 1

    # PyInstaller へ日本語パスを渡さないよう、同梱用 PNG は ASCII 名で build に出力する
    if not image.save(str(runtime_png_path), "PNG"):
        print(f"failed to save png: {runtime_png_path}", file=sys.stderr)
        return 1

    print(ico_path)
    return 0


def _write_multi_size_ico(image: QImage, ico_path: Path) -> bool:
    sizes = [16, 32, 48, 64, 128, 256]
    image_blobs: list[bytes] = []
    entries: list[tuple[int, int, int, int, int]] = []

    for size in sizes:
        scaled = image.scaled(size, size)
        buffer = QByteArray()
        qbuffer = QBuffer(buffer)
        if not qbuffer.open(QIODevice.OpenModeFlag.WriteOnly):
            return False
        if not scaled.save(qbuffer, "PNG"):
            return False
        blob = bytes(buffer)
        image_blobs.append(blob)
        entries.append((size, size, len(blob), 0))

    header = struct.pack("<HHH", 0, 1, len(image_blobs))
    directory = bytearray()
    offset = 6 + (16 * len(image_blobs))
    for (size, height, length, _reserved), blob in zip(entries, image_blobs):
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                size if size < 256 else 0,
                height if height < 256 else 0,
                0,
                0,
                1,
                32,
                length,
                offset,
            )
        )
        offset += length

    with ico_path.open("wb") as fh:
        fh.write(header)
        fh.write(directory)
        for blob in image_blobs:
            fh.write(blob)
    return True


if __name__ == "__main__":
    raise SystemExit(main())
