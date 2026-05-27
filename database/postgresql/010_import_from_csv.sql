SET search_path TO public;

-- psql variable example:
-- \set csv_dir 'C:/temp/defect_information_search_export'
-- \copy defect_records FROM :'csv_dir'/defect_records.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
-- \copy inspection_records FROM :'csv_dir'/inspection_records.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
-- \copy inspector_master FROM :'csv_dir'/inspector_master.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
-- \copy product_catalog FROM :'csv_dir'/product_catalog.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
-- \copy product_master FROM :'csv_dir'/product_master.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
-- \copy qr_history FROM :'csv_dir'/qr_history.csv WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
