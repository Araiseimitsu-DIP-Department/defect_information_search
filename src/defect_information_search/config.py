from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


APP_NAME = "不具合情報検索"


@dataclass(frozen=True)
class AppConfig:
    access_db_path: Path

    @classmethod
    def load(cls, base_dir: Path, extra_dirs: Iterable[Path] | None = None) -> "AppConfig":
        search_dirs = [base_dir, *(extra_dirs or [])]
        for env_path in cls._candidate_env_paths(search_dirs):
            if env_path.exists():
                load_dotenv(env_path, override=False)
                break
        db_path = os.getenv("ACCESS_DB_PATH", "").strip().strip('"')
        if db_path.startswith("\\") and not db_path.startswith("\\\\"):
            db_path = "\\" + db_path
        if not db_path:
            raise ValueError(
                "ACCESS_DB_PATH が見つかりません。"
                "\n.exe と同じフォルダ、または 1 つ上のフォルダに .env を置くか、"
                "環境変数 ACCESS_DB_PATH を設定してください。"
            )
        return cls(access_db_path=Path(db_path))

    @staticmethod
    def _candidate_env_paths(search_dirs: Iterable[Path]) -> list[Path]:
        candidates: list[Path] = []
        for search_dir in search_dirs:
            candidates.append(search_dir / ".env")
            candidates.append(search_dir.parent / ".env")
        candidates.append(Path.cwd() / ".env")
        unique_candidates: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate.resolve(strict=False)).casefold()
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)
        return unique_candidates
