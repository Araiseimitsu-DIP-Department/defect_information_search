import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from defect_information_search.config import APP_VERSION
from defect_information_search.webview.bridge import WebviewBridge


class AppVersionTests(unittest.TestCase):
    def test_bootstrap_returns_current_version(self) -> None:
        bridge = WebviewBridge(Mock(), Mock())

        result = bridge.bootstrap()

        self.assertEqual(APP_VERSION, "1.1.0")
        self.assertEqual(result["app_version"], APP_VERSION)
