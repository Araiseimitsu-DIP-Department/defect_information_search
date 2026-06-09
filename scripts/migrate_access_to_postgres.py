from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from defect_information_search.config import AppConfig
from defect_information_search.infrastructure.access_gateway import AccessGateway


SQL_DIR = ROOT_DIR / "database" / "postgresql"


@dataclass(frozen=True)
class TableMigration:
    source_table: str
    target_table: str
    columns: Sequence[str]
    mapper: Any
    expected_rows: int | None = None


DEFECT_COUNT_COLUMNS = [
    ("外観キズ", "appearance_scratch"),
    ("圧痕", "dent"),
    ("切粉", "chip"),
    ("毟れ", "tear"),
    ("穴大", "hole_large"),
    ("穴小", "hole_small"),
    ("穴キズ", "hole_scratch"),
    ("バリ", "burr"),
    ("短寸", "short_length"),
    ("面粗", "rough_surface"),
    ("サビ", "rust"),
    ("ボケ", "blur"),
    ("挽目", "turning_mark"),
    ("汚れ", "stain"),
    ("メッキ", "plating"),
    ("落下", "drop_damage"),
    ("フクレ", "blister"),
    ("ツブレ", "crush"),
    ("ボッチ", "projection"),
    ("段差", "step"),
    ("バレル石", "barrel_stone"),
    ("径プラス", "diameter_plus"),
    ("径マイナス", "diameter_minus"),
    ("ゲージ", "gauge"),
    ("異物混入", "foreign_matter"),
    ("形状不良", "shape_defect"),
    ("こすれ", "rub_mark"),
    ("変色シミ", "discoloration"),
    ("材料キズ", "material_scratch"),
    ("ゴミ", "dust"),
    ("その他", "other"),
]


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return max(int(float(value)), 0)
    except (TypeError, ValueError):
        return None


def clean_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_bool(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "-1"}


def clean_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def clean_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def map_defect_record(row: dict[str, Any]) -> tuple[Any, ...]:
    values: list[Any] = [
        clean_int(row.get("ID")),
        clean_text(row.get("生産ロットID")),
        clean_text(row.get("品番")),
        clean_date(row.get("指示日")),
        clean_text(row.get("号機")),
        clean_text(row.get("検査者1")),
        clean_text(row.get("検査者2")),
        clean_text(row.get("検査者3")),
        clean_text(row.get("検査者4")),
        clean_text(row.get("検査者5")),
        clean_int(row.get("時間")),
        clean_int(row.get("数量")),
        clean_int(row.get("総不具合数")),
        clean_float(row.get("不良率")),
    ]
    values.extend(clean_int(row.get(source)) for source, _ in DEFECT_COUNT_COLUMNS)
    values.append(clean_text(row.get("その他内容")))
    return tuple(values)


def map_inspection_record(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        clean_int(row.get("ID")),
        clean_datetime(row.get("日付時刻")),
        clean_text(row.get("生産ロットID")),
        clean_text(row.get("検査員ID")),
        clean_text(row.get("工程名")),
        clean_text(row.get("号機")),
    )


def map_inspector_master(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        clean_text(row.get("検査員ID")),
        clean_text(row.get("検査員名")),
        clean_text(row.get("区別")),
        clean_bool(row.get("表示フラグ")),
    )


def map_product_catalog(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        clean_text(row.get("生産ロットID")),
        clean_text(row.get("号機")),
        clean_text(row.get("品番")),
        clean_text(row.get("品名")),
        clean_text(row.get("客先")),
        clean_date(row.get("指示日")),
        clean_int(row.get("数量")),
    )


def map_product_master(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        clean_text(row.get("製品番号")),
        clean_text(row.get("製品名")),
        clean_text(row.get("客先名")),
        clean_text(row.get("担当")),
        clean_text(row.get("材質")),
        clean_text(row.get("指示書有無")),
        clean_text(row.get("洗浄1")),
        clean_text(row.get("工程2")),
        clean_text(row.get("工程3")),
        clean_text(row.get("工程4")),
        clean_text(row.get("工程5")),
        clean_text(row.get("工程6")),
        clean_text(row.get("工程7")),
        clean_text(row.get("工程8")),
        clean_text(row.get("工程9")),
        clean_text(row.get("梱包形態")),
        clean_text(row.get("梱包仕様")),
        clean_text(row.get("送り先指定")),
        clean_text(row.get("製品ID")),
        clean_text(row.get("工程2備考")),
        clean_text(row.get("工程3備考")),
        clean_text(row.get("工程4備考")),
        clean_text(row.get("工程5備考")),
        clean_text(row.get("工程6備考")),
        clean_text(row.get("工程7備考")),
        clean_text(row.get("工程8備考")),
        clean_text(row.get("工程9備考")),
        clean_float(row.get("単価")),
        clean_int(row.get("材料識別")),
        clean_text(row.get("製品取扱注意事項")),
        clean_text(row.get("次工程")),
        clean_text(row.get("呼出コード")),
        clean_float(row.get("製品単重")),
        clean_text(row.get("工程2集計")),
        clean_text(row.get("工程3集計")),
        clean_text(row.get("工程4集計")),
        clean_text(row.get("工程5集計")),
        clean_text(row.get("工程6集計")),
        clean_text(row.get("工程7集計")),
        clean_text(row.get("工程8集計")),
    )


def map_qr_history(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        clean_int(row.get("ID")),
        clean_datetime(row.get("日付時刻")),
        clean_text(row.get("QRコード")),
        clean_text(row.get("生産ロットID")),
        clean_datetime(row.get("日付")),
        clean_text(row.get("工程")),
        clean_text(row.get("位置")),
        clean_int(row.get("数量")),
        clean_text(row.get("工程コード")),
        clean_text(row.get("工程名")),
        clean_text(row.get("更新フラグ")),
    )


MIGRATIONS = [
    TableMigration(
        "t_QR履歴",
        "qr_history",
        (
            "id",
            "recorded_at",
            "qr_code",
            "production_lot_id",
            "event_at",
            "process",
            "position",
            "quantity",
            "process_code",
            "process_name",
            "updated_flag",
        ),
        map_qr_history,
        108168,
    ),
    TableMigration(
        "t_不具合情報",
        "defect_records",
        (
            "id",
            "production_lot_id",
            "part_number",
            "instruction_date",
            "machine_no",
            "inspector_1",
            "inspector_2",
            "inspector_3",
            "inspector_4",
            "inspector_5",
            "work_minutes",
            "quantity",
            "total_defect_count",
            "defect_rate",
            *(target for _, target in DEFECT_COUNT_COLUMNS),
            "other_detail",
        ),
        map_defect_record,
        154834,
    ),
    TableMigration(
        "t_数値検査員マスタ",
        "inspector_master",
        ("inspector_id", "inspector_name", "category", "visible"),
        map_inspector_master,
        14,
    ),
    TableMigration(
        "t_数値検査記録",
        "inspection_records",
        ("id", "recorded_at", "production_lot_id", "inspector_id", "process_name", "machine_no"),
        map_inspection_record,
        24846,
    ),
    TableMigration(
        "t_現品票検索用",
        "product_catalog",
        ("production_lot_id", "machine_no", "part_number", "part_name", "customer_name", "instruction_date", "quantity"),
        map_product_catalog,
        168782,
    ),
    TableMigration(
        "t_製品マスタ",
        "product_master",
        (
            "product_number",
            "product_name",
            "customer_name",
            "person_in_charge",
            "material",
            "has_instruction_sheet",
            "washing_1",
            "process_2",
            "process_3",
            "process_4",
            "process_5",
            "process_6",
            "process_7",
            "process_8",
            "process_9",
            "packing_type",
            "packing_spec",
            "shipping_destination",
            "product_id",
            "process_2_note",
            "process_3_note",
            "process_4_note",
            "process_5_note",
            "process_6_note",
            "process_7_note",
            "process_8_note",
            "process_9_note",
            "unit_price",
            "material_type",
            "handling_note",
            "next_process",
            "call_code",
            "unit_weight",
            "process_2_summary",
            "process_3_summary",
            "process_4_summary",
            "process_5_summary",
            "process_6_summary",
            "process_7_summary",
            "process_8_summary",
        ),
        map_product_master,
        1502,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Access data to PostgreSQL.")
    parser.add_argument("--dry-run", action="store_true", help="Read Access and transform samples without writing PostgreSQL.")
    parser.add_argument("--apply", action="store_true", help="Write transformed rows to PostgreSQL.")
    parser.add_argument("--apply-schema", action="store_true", help="Apply 001_schema.sql before loading data.")
    parser.add_argument("--truncate", action="store_true", help="Truncate target tables before loading data.")
    parser.add_argument("--sample-size", type=int, default=3, help="Rows to transform per table during dry-run.")
    parser.add_argument("--batch-size", type=int, default=5000, help="PostgreSQL insert batch size.")
    return parser.parse_args()


def row_to_dict(columns: Sequence[str], row: Sequence[Any]) -> dict[str, Any]:
    return dict(zip(columns, row, strict=False))


def access_count(gateway: AccessGateway, table_name: str) -> int:
    frame = gateway.fetch_dataframe(f"SELECT COUNT(*) AS row_count FROM [{table_name}]")
    return int(frame.iloc[0]["row_count"])


def stream_transformed_rows(gateway: AccessGateway, migration: TableMigration) -> Iterator[tuple[Any, ...]]:
    with gateway.stream_rows(f"SELECT * FROM [{migration.source_table}]") as stream:
        for row in stream:
            yield migration.mapper(row_to_dict(stream.columns, row))


def transformed_samples(gateway: AccessGateway, migration: TableMigration, sample_size: int) -> list[tuple[Any, ...]]:
    frame = gateway.fetch_dataframe(f"SELECT TOP {sample_size} * FROM [{migration.source_table}]")
    return [migration.mapper(row) for row in frame.to_dict("records")]


def run_dry_run(gateway: AccessGateway, sample_size: int) -> int:
    print("Dry-run: Access read and transform check")
    for migration in MIGRATIONS:
        count = access_count(gateway, migration.source_table)
        expected = migration.expected_rows
        status = "OK" if expected is None or count == expected else f"DOCS {expected}"
        print(f"{migration.target_table}: {count} rows ({status})")
        samples = transformed_samples(gateway, migration, sample_size)
        if samples:
            print(f"  sample columns={len(samples[0])}, rows={len(samples)}")
    return 0


def require_psycopg():
    try:
        import psycopg
        from psycopg import sql
    except ImportError as exc:
        raise SystemExit("psycopg is required for --apply. Install requirements first.") from exc
    return psycopg, sql


def apply_schema(connection: Any) -> None:
    schema_sql = (SQL_DIR / "001_schema.sql").read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(schema_sql)
    connection.commit()


def truncate_tables(connection: Any, sql_module: Any) -> None:
    table_names = [migration.target_table for migration in MIGRATIONS]
    identifiers = [sql_module.Identifier(table_name) for table_name in table_names]
    statement = sql_module.SQL("TRUNCATE TABLE {} RESTART IDENTITY").format(
        sql_module.SQL(", ").join(identifiers)
    )
    with connection.cursor() as cursor:
        cursor.execute(statement)
    connection.commit()


def insert_batch(connection: Any, sql_module: Any, migration: TableMigration, rows: Sequence[tuple[Any, ...]]) -> None:
    placeholders = sql_module.SQL(", ").join(sql_module.Placeholder() for _ in migration.columns)
    columns = sql_module.SQL(", ").join(sql_module.Identifier(column) for column in migration.columns)
    statement = sql_module.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql_module.Identifier(migration.target_table),
        columns,
        placeholders,
    )
    with connection.cursor() as cursor:
        cursor.executemany(statement, rows)


def batched(rows: Iterable[tuple[Any, ...]], batch_size: int) -> Iterator[list[tuple[Any, ...]]]:
    batch: list[tuple[Any, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def ensure_inspection_inspectors(connection: Any, sql_module: Any, gateway: AccessGateway) -> None:
    inspection_migration = next(migration for migration in MIGRATIONS if migration.target_table == "inspection_records")
    source_ids = {
        row[3]
        for row in stream_transformed_rows(gateway, inspection_migration)
        if row[3] is not None
    }
    if not source_ids:
        return

    with connection.cursor() as cursor:
        cursor.execute("SELECT inspector_id FROM inspector_master")
        existing_ids = {row[0] for row in cursor.fetchall()}

    missing_ids = sorted(source_ids - existing_ids)
    if not missing_ids:
        return

    statement = sql_module.SQL(
        "INSERT INTO inspector_master (inspector_id, visible) VALUES ({}, {}) "
        "ON CONFLICT (inspector_id) DO NOTHING"
    ).format(sql_module.Placeholder(), sql_module.Placeholder())
    rows = [(inspector_id, False) for inspector_id in missing_ids]
    with connection.cursor() as cursor:
        cursor.executemany(statement, rows)
    connection.commit()
    print(f"inspector_master: added {len(rows)} placeholder inspector ids")


def run_apply(config: AppConfig, gateway: AccessGateway, args: argparse.Namespace) -> int:
    if not config.postgres_dsn:
        raise SystemExit("POSTGRES_CONNECTION_URL is required for --apply.")

    psycopg, sql_module = require_psycopg()
    with psycopg.connect(config.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql_module.SQL("SET search_path TO {}").format(sql_module.Identifier(config.postgres_schema))
            )
        if args.apply_schema:
            apply_schema(connection)
        if args.truncate:
            truncate_tables(connection, sql_module)

        for migration in MIGRATIONS:
            if migration.target_table == "inspection_records":
                ensure_inspection_inspectors(connection, sql_module, gateway)

            written = 0
            for batch in batched(stream_transformed_rows(gateway, migration), args.batch_size):
                insert_batch(connection, sql_module, migration, batch)
                written += len(batch)
                print(f"{migration.target_table}: inserted {written} rows")
            connection.commit()
    return 0


def main() -> int:
    args = parse_args()
    if not args.dry_run and not args.apply:
        args.dry_run = True

    config = AppConfig.load(ROOT_DIR)
    gateway = AccessGateway(config.access_db_path)

    if args.dry_run:
        return run_dry_run(gateway, args.sample_size)
    return run_apply(config, gateway, args)


if __name__ == "__main__":
    raise SystemExit(main())
