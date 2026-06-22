# PostgreSQL Migration Notes

## Current Runtime Status

- Status: application runtime updated for the split PostgreSQL databases. Product search now reads from `delivery_label_db.public.delivery_label_history` and uses case-insensitive matching.
- Runtime DBs:
  - `appearance_inspection_db`
  - `delivery_label_db`
  - `arai_masters`
- Runtime repository: `src/defect_information_search/infrastructure/postgres/defect_repository.py`
- Access query behavior is handled in Python, not by PostgreSQL views.
- `t_製品マスタ` is now read from `arai_masters.public.product_master`.
- Product master lookup uses only the required columns from `arai_masters.product_master`, with product matching on `product_no`.

## Runtime Smoke Test

- Command: `.\.venv\Scripts\python.exe scripts\smoke_test_postgres_repository.py`
- Result:
  - `products`: 6
  - `defects_for_part`: 23644
  - `defects_for_part_non_null_work_minutes`: 23614
  - `defects_between`: 106373
  - `qr_lots`: 23809
  - `lot_defects`: 5
  - `product_masters`: 1
  - `iter_columns`: 47
  - `iter_sample_rows`: 3

## Split DB Mapping

| Purpose | DB | Table |
|---|---|---|
| Defect records | `appearance_inspection_db` | `defect_information` |
| Numeric inspector lookup | `appearance_inspection_db` | `numeric_inspection_records`, `numeric_inspector_master` |
| QR disposal lots | `delivery_label_db` | `qr_history` |
| Product search candidates | `delivery_label_db` | `delivery_label_history` |
| Product master | `arai_masters` | `product_master` |

## Legacy Single-DB Migration Notes

The notes below describe the earlier migration into a single `defect_information_search` PostgreSQL database. These files are retained as legacy migration assets, but the current application runtime no longer depends on the unified tables such as `defect_records`, `inspection_records`, `product_catalog`, or the old `product_master` shape.

### Dry-run

- Status: completed locally
- Command: `.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run`
- Result:
  - `qr_history`: 108,188 rows
  - `defect_records`: 154,836 rows
  - `inspector_master`: 14 rows
  - `inspection_records`: 24,943 rows
  - `product_catalog`: 168,834 rows
  - `product_master`: 1,502 rows
- Note: counts differ slightly from the static docs snapshot because the Access source changed after that snapshot.

### Apply

- Status: completed
- Command: `.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply --apply-schema`
- Result:
  - `qr_history`: 108,293 rows inserted
  - `defect_records`: 154,862 rows inserted
  - `inspector_master`: 14 rows inserted
  - `inspection_records`: 24,943 rows inserted
  - `product_catalog`: 168,837 rows inserted
  - `product_master`: 1,502 rows inserted
- Indexes: applied with `database/postgresql/002_indexes.sql`
- Constraints: applied with `database/postgresql/003_constraints.sql`; historical nonnegative CHECK constraints are `NOT VALID`
- Validation:
  - duplicate IDs: 0 for `defect_records`, `inspection_records`, `qr_history`
  - blank `defect_records.part_number`: 3
  - blank `defect_records.production_lot_id`: 3
  - missing `inspection_records.inspector_id` references: 26
  - missing `defect_records.part_number` references in `product_master`: 24,781
  - missing `defect_records.production_lot_id` references in `product_catalog`: 12
  - `qr_history.process_code = '03'`: 23,370
  - app detail search candidates: 106,088

### Sequence Adjustment

- Status: completed
- Result:
  - `defect_records`: sequence set to 155,048
  - `inspection_records`: sequence set to 25,059
  - `qr_history`: sequence set to 108,293

### Final Validation

- Status: completed
- Result:
  - `inspector_master`: 14 rows
  - `product_master`: 1,502 rows
  - `inspection_records`: 24,943 rows
  - `qr_history`: 108,293 rows
  - `defect_records`: 154,862 rows
  - `product_catalog`: 168,837 rows
  - duplicate IDs: 0
  - blank `defect_records.part_number`: 3
  - blank `defect_records.production_lot_id`: 3
  - blank `product_master.product_number`: 0
  - blank `inspector_master.inspector_id`: 0
  - missing `inspection_records.inspector_id` references: 26
  - missing `defect_records.part_number` references in `product_master`: 24,781
  - missing `defect_records.production_lot_id` references in `product_catalog`: 12
  - `qr_history.process_code = '03'`: 23,370
  - app detail search candidates: 106,088
