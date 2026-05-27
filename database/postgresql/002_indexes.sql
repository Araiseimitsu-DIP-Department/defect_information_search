SET search_path TO public;

CREATE INDEX IF NOT EXISTS idx_defect_records_part_number ON defect_records (part_number);
CREATE INDEX IF NOT EXISTS idx_defect_records_instruction_date ON defect_records (instruction_date);
CREATE INDEX IF NOT EXISTS idx_defect_records_lot_id ON defect_records (production_lot_id);
CREATE INDEX IF NOT EXISTS idx_defect_records_machine_no ON defect_records (machine_no);
CREATE INDEX IF NOT EXISTS idx_defect_records_total_defect_count ON defect_records (total_defect_count);

CREATE INDEX IF NOT EXISTS idx_inspection_records_lot_id ON inspection_records (production_lot_id);
CREATE INDEX IF NOT EXISTS idx_inspection_records_inspector_id ON inspection_records (inspector_id);

CREATE INDEX IF NOT EXISTS idx_inspector_master_inspector_id ON inspector_master (inspector_id);

CREATE INDEX IF NOT EXISTS idx_product_catalog_lot_id ON product_catalog (production_lot_id);
CREATE INDEX IF NOT EXISTS idx_product_catalog_part_number ON product_catalog (part_number);
CREATE INDEX IF NOT EXISTS idx_product_catalog_part_name ON product_catalog (part_name);
CREATE INDEX IF NOT EXISTS idx_product_catalog_customer_name ON product_catalog (customer_name);

CREATE INDEX IF NOT EXISTS idx_product_master_product_number ON product_master (product_number);
CREATE INDEX IF NOT EXISTS idx_product_master_customer_name ON product_master (customer_name);
CREATE INDEX IF NOT EXISTS idx_product_master_material ON product_master (material);

CREATE INDEX IF NOT EXISTS idx_qr_history_event_at ON qr_history (event_at);
CREATE INDEX IF NOT EXISTS idx_qr_history_process_code ON qr_history (process_code);
CREATE INDEX IF NOT EXISTS idx_qr_history_lot_id ON qr_history (production_lot_id);
