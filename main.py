from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _patch_six_meta_path_importer() -> None:
    try:
        import six
    except Exception:
        return

    for finder in sys.meta_path:
        if finder.__class__.__name__ == "_SixMetaPathImporter" and not hasattr(finder, "_path"):
            finder._path = []  # type: ignore[attr-defined]


_patch_six_meta_path_importer()

from defect_information_search.app import main


if __name__ == "__main__":
    raise SystemExit(main())
