SET search_path TO public;

ALTER TABLE defect_records
    ADD CONSTRAINT pk_defect_records PRIMARY KEY (id);

ALTER TABLE inspection_records
    ADD CONSTRAINT pk_inspection_records PRIMARY KEY (id);

ALTER TABLE qr_history
    ADD CONSTRAINT pk_qr_history PRIMARY KEY (id);

ALTER TABLE inspector_master
    ADD CONSTRAINT pk_inspector_master PRIMARY KEY (inspector_id);

ALTER TABLE product_master
    ADD CONSTRAINT pk_product_master PRIMARY KEY (product_number);

ALTER TABLE defect_records
    ADD CONSTRAINT ck_defect_records_nonnegative_counts CHECK (
        coalesce(quantity, 0) >= 0
        AND coalesce(total_defect_count, 0) >= 0
        AND coalesce(appearance_scratch, 0) >= 0
        AND coalesce(dent, 0) >= 0
        AND coalesce(chip, 0) >= 0
        AND coalesce(tear, 0) >= 0
        AND coalesce(hole_large, 0) >= 0
        AND coalesce(hole_small, 0) >= 0
        AND coalesce(hole_scratch, 0) >= 0
        AND coalesce(burr, 0) >= 0
        AND coalesce(short_length, 0) >= 0
        AND coalesce(rough_surface, 0) >= 0
        AND coalesce(rust, 0) >= 0
        AND coalesce(blur, 0) >= 0
        AND coalesce(turning_mark, 0) >= 0
        AND coalesce(stain, 0) >= 0
        AND coalesce(plating, 0) >= 0
        AND coalesce(drop_damage, 0) >= 0
        AND coalesce(blister, 0) >= 0
        AND coalesce(crush, 0) >= 0
        AND coalesce(projection, 0) >= 0
        AND coalesce(step, 0) >= 0
        AND coalesce(barrel_stone, 0) >= 0
        AND coalesce(diameter_plus, 0) >= 0
        AND coalesce(diameter_minus, 0) >= 0
        AND coalesce(gauge, 0) >= 0
        AND coalesce(foreign_matter, 0) >= 0
        AND coalesce(shape_defect, 0) >= 0
        AND coalesce(rub_mark, 0) >= 0
        AND coalesce(discoloration, 0) >= 0
        AND coalesce(material_scratch, 0) >= 0
        AND coalesce(dust, 0) >= 0
        AND coalesce(other, 0) >= 0
    ) NOT VALID;

ALTER TABLE product_catalog
    ADD CONSTRAINT ck_product_catalog_quantity_nonnegative CHECK (coalesce(quantity, 0) >= 0) NOT VALID;

ALTER TABLE qr_history
    ADD CONSTRAINT ck_qr_history_quantity_nonnegative CHECK (coalesce(quantity, 0) >= 0) NOT VALID;

ALTER TABLE inspection_records
    ADD CONSTRAINT fk_inspection_records_inspector
    FOREIGN KEY (inspector_id) REFERENCES inspector_master (inspector_id)
    NOT VALID;
