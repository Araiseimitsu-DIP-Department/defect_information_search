SET search_path TO public;

SELECT 'defect_records' AS check_name, count(*) AS value FROM defect_records
UNION ALL SELECT 'inspection_records', count(*) FROM inspection_records
UNION ALL SELECT 'inspector_master', count(*) FROM inspector_master
UNION ALL SELECT 'product_catalog', count(*) FROM product_catalog
UNION ALL SELECT 'product_master', count(*) FROM product_master
UNION ALL SELECT 'qr_history', count(*) FROM qr_history;

SELECT 'defect_records.id duplicates' AS check_name, count(*) AS value
FROM (SELECT id FROM defect_records GROUP BY id HAVING count(*) > 1) duplicated;

SELECT 'inspection_records.id duplicates' AS check_name, count(*) AS value
FROM (SELECT id FROM inspection_records GROUP BY id HAVING count(*) > 1) duplicated;

SELECT 'qr_history.id duplicates' AS check_name, count(*) AS value
FROM (SELECT id FROM qr_history GROUP BY id HAVING count(*) > 1) duplicated;

SELECT 'defect_records.part_number blank' AS check_name, count(*) AS value
FROM defect_records
WHERE nullif(btrim(part_number), '') IS NULL;

SELECT 'defect_records.production_lot_id blank' AS check_name, count(*) AS value
FROM defect_records
WHERE nullif(btrim(production_lot_id), '') IS NULL;

SELECT 'product_master.product_number blank' AS check_name, count(*) AS value
FROM product_master
WHERE nullif(btrim(product_number), '') IS NULL;

SELECT 'inspector_master.inspector_id blank' AS check_name, count(*) AS value
FROM inspector_master
WHERE nullif(btrim(inspector_id), '') IS NULL;

SELECT 'inspection_records missing inspector' AS check_name, count(*) AS value
FROM inspection_records r
LEFT JOIN inspector_master m ON m.inspector_id = r.inspector_id
WHERE nullif(btrim(r.inspector_id), '') IS NOT NULL
  AND m.inspector_id IS NULL;

SELECT 'defect_records missing product_master' AS check_name, count(*) AS value
FROM defect_records d
LEFT JOIN product_master p ON p.product_number = d.part_number
WHERE nullif(btrim(d.part_number), '') IS NOT NULL
  AND p.product_number IS NULL;

SELECT 'defect_records missing product_catalog lot' AS check_name, count(*) AS value
FROM defect_records d
LEFT JOIN product_catalog c ON c.production_lot_id = d.production_lot_id
WHERE nullif(btrim(d.production_lot_id), '') IS NOT NULL
  AND c.production_lot_id IS NULL;

SELECT 'qr_history process_code 03' AS check_name, count(*) AS value
FROM qr_history
WHERE process_code = '03';

SELECT 'app detail search candidates' AS check_name, count(*) AS value
FROM defect_records
WHERE production_lot_id LIKE 'P%'
  AND coalesce(total_defect_count, 0) > 0;
