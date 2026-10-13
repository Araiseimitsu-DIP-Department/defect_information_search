"""Prepare bundled settings and inspect the actual onefile archive without logging secrets."""
from __future__ import annotations

import argparse
import io
from pathlib import Path

from dotenv import dotenv_values


ACCESS_MODULES = (
    "pyodbc", "pypyodbc",
    "defect_information_search.infrastructure.access",
    "defect_information_search.infrastructure.access_gateway",
)


def prepare(source: Path, destination: Path, backend: str) -> None:
    values = dotenv_values(source, encoding="utf-8-sig", interpolate=False)
    configured = (values.get("DB_BACKEND") or values.get("DATABASE_BACKEND") or "access").strip().lower()
    if configured != backend:
        raise ValueError("The .env backend must match -Backend; source settings were not modified.")
    if backend == "access":
        destination.write_bytes(source.read_bytes())
    else:
        # Preserve unrelated variables used by ${...} interpolation, but omit Access settings/comments.
        values = {k: v for k, v in values.items() if not k.startswith("ACCESS_") and k not in {"DB_BACKEND", "DATABASE_BACKEND"}}
        values["DB_BACKEND"] = "postgres"
        lines = []
        for key, value in values.items():
            if value is None:
                lines.append(key)
            else:
                escaped = value.replace("\\", "\\\\").replace("'", "\\'")
                lines.append(f"{key}='{escaped}'")
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    destination.with_name("build_backend.txt").write_text(backend, encoding="utf-8")


def verify(executable: Path, backend: str) -> None:
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(executable))
    modules = set(archive.open_embedded_archive("PYZ.pyz").toc)
    files = {name.replace("\\", "/").lower() for name in archive.toc}
    required = {"psycopg", "psycopg_binary", "pandas", "openpyxl", "webview.platforms.edgechromium", "webview.platforms.winforms", "webview.platforms.win32", "defect_information_search.infrastructure.postgres.defect_repository"}
    if not required <= modules:
        raise ValueError("Required runtime modules missing: " + ", ".join(sorted(required - modules)))
    assets = "defect_information_search/webview/assets/"
    if not {".env", "build_backend.txt", "app_icon.ico", *(assets + name for name in ("index.html", "app.js", "styles.css", "arai_logo.png"))} <= files:
        raise ValueError("Required runtime assets missing")
    if archive.extract("build_backend.txt").decode("utf-8") != backend:
        raise ValueError("Build backend marker mismatch")
    values = dotenv_values(stream=io.StringIO(archive.extract(".env").decode("utf-8-sig")), interpolate=False)
    if backend == "postgres":
        forbidden = {m for m in modules if any(m == prefix or m.startswith(prefix + ".") for prefix in ACCESS_MODULES)}
        unwanted = {f for f in files if f.endswith((".accdb", ".mdb", ".laccdb", ".ldb")) or any(token in f for token in ("pyodbc", "pypyodbc", "aceodbc", "aceoledb", "msaccess"))}
        if forbidden or unwanted:
            raise ValueError("Access dependencies found: " + ", ".join(sorted(forbidden | unwanted)))
        if any(k.startswith("ACCESS_") for k in values) or values.get("DB_BACKEND") != "postgres":
            raise ValueError("Bundled settings are not PostgreSQL-only")
    elif not any("pyodbc" in f and f.endswith(".pyd") for f in files) or "defect_information_search.infrastructure.access.defect_repository" not in modules:
        raise ValueError("Access build is missing Access dependencies")
    print(f"Archive verification PASS ({backend}), {executable.stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "verify"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--backend", choices=("postgres", "access"), required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "prepare":
            if args.destination is None:
                parser.error("prepare requires --destination")
            prepare(args.path, args.destination, args.backend)
        else:
            verify(args.path, args.backend)
    except Exception:
        # Do not expose dotenv contents, credentials, or connection strings on failures.
        raise SystemExit("Build settings/archive validation failed; check backend and required dependencies.") from None


if __name__ == "__main__":
    main()
