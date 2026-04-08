from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_NAME = "不具合情報検索"


@dataclass(frozen=True)
class AppConfig:
    access_db_path: Path

    @classmethod
    def load(cls, base_dir: Path) -> "AppConfig":
        load_dotenv(base_dir / ".env")
        db_path = os.getenv("ACCESS_DB_PATH", "").strip().strip('"')
        if db_path.startswith("\\") and not db_path.startswith("\\\\"):
            db_path = "\\" + db_path
        if not db_path:
            raise ValueError(".env に ACCESS_DB_PATH を設定してください。")
        return cls(access_db_path=Path(db_path))
