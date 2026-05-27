# PostgreSQL Migration Notes

## Dry-run

- Status: completed locally
- Command: `.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run`
- Result:
  - `qr_history`: 108,188 rows
  - `defect_records`: 154,836 rows
  - `inspector_master`: 14 rows
  - `inspection_records`: 24,943 rows
  - `product_catalog`: 168,834 rows
  - `product_master`: 1,502 rows
- Note: counts differ slightly from the static docs snapshot because the Access source has changed since that snapshot.

## Apply

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
- Remaining:
  - review source data quality findings before adding validated FK constraints

## Sequence Adjustment

- Status: completed
- Result:
  - `defect_records`: sequence set to 155,048
  - `inspection_records`: sequence set to 25,059
  - `qr_history`: sequence set to 108,293

## Final Validation

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
