from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    load_dotenv(Path.cwd() / ".env", override=True)
    connection_url = os.getenv("POSTGRES_CONNECTION_URL")
    if not connection_url:
        raise SystemExit("POSTGRES_CONNECTION_URL is not set.")

    import psycopg

    parsed = urlparse(connection_url)
    connection_kwargs = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/"),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "connect_timeout": 30,
    }

    tables = ("defect_records", "inspection_records", "qr_history")
    with psycopg.connect(**connection_kwargs) as connection:
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('public.{table}', 'id'),
                        coalesce((SELECT max(id) FROM public.{table}), 1),
                        true
                    )
                    """
                )
                print(f"{table}: sequence={cursor.fetchone()[0]}")
        connection.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
