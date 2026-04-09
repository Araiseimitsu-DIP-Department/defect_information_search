import sys


for finder in sys.meta_path:
    if finder.__class__.__name__ == "_SixMetaPathImporter" and not hasattr(finder, "_path"):
        finder._path = []
