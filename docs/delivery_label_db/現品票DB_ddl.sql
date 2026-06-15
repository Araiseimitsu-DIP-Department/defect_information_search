-- PostgreSQL DDL 草案（Access メタデータから自動生成）
-- ※ 型・制約は必ず手動で確認・修正してください

CREATE TABLE "t_ExcelQR履歴" (
    "日付時刻" TIMESTAMP,
    "QRコード" VARCHAR(22),
    "生産ロットID" VARCHAR(7),
    "日付" TIMESTAMP,
    "工程" VARCHAR(2),
    "位置" VARCHAR(2),
    "数量" INTEGER,
    "工程名" VARCHAR(30)
);


CREATE TABLE "t_Excel現品票履歴" (
    "生産ロットID" VARCHAR(7),
    "号機" VARCHAR(5),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "客先" VARCHAR(30),
    "材質" VARCHAR(50),
    "材料ロットNO" VARCHAR(30),
    "数量" INTEGER,
    "備考" VARCHAR(50),
    "指示日" TIMESTAMP,
    "完了フラグ" VARCHAR(1)
);


CREATE TABLE "t_ID番号" (
    "ID" BIGSERIAL,
    "P番号" INTEGER,
    "E番号" INTEGER
);


CREATE TABLE "t_QR履歴" (
    "日付時刻" TIMESTAMP,
    "QRコード" VARCHAR(22),
    "生産ロットID" VARCHAR(7),
    "日付" TIMESTAMP,
    "工程" VARCHAR(2),
    "位置" VARCHAR(2),
    "数量" INTEGER,
    "工程コード" VARCHAR(2),
    "工程名" VARCHAR(30),
    "更新フラグ" VARCHAR(1),
    "ID" BIGSERIAL
);


CREATE TABLE "t_QR履歴(backup_260521)" (
    "日付時刻" TIMESTAMP,
    "QRコード" VARCHAR(22),
    "生産ロットID" VARCHAR(7),
    "日付" TIMESTAMP,
    "工程" VARCHAR(2),
    "位置" VARCHAR(2),
    "数量" INTEGER,
    "工程コード" VARCHAR(2),
    "工程名" VARCHAR(30),
    "更新フラグ" VARCHAR(1)
);


CREATE TABLE "t_QR履歴Tmp" (
    "日付時刻" TIMESTAMP,
    "QRコード" VARCHAR(22),
    "生産ロットID" VARCHAR(7),
    "日付" TIMESTAMP,
    "工程" VARCHAR(2),
    "位置" VARCHAR(2),
    "数量" INTEGER,
    "更新フラグ" VARCHAR(1),
    "TNo" VARCHAR(1)
);


CREATE TABLE "t_エラーログ" (
    "ID" BIGSERIAL,
    "日付" TIMESTAMP,
    "生産ロットID" VARCHAR(7),
    "エラー内容" VARCHAR(20)
);


CREATE TABLE "t_ロット完了理由" (
    "理由コード" VARCHAR(1),
    "理由" VARCHAR(5)
);


CREATE TABLE "t_作業履歴" (
    "ID" BIGSERIAL,
    "ロット数数値検査" INTEGER,
    "ロット数外観検査" INTEGER,
    "ロット数梱包" INTEGER,
    "ロット数洗浄" INTEGER,
    "ロット数二次作業" INTEGER,
    "個数数値検査" INTEGER,
    "個数外観検査" INTEGER,
    "個数梱包" INTEGER,
    "個数洗浄" INTEGER,
    "個数二次作業" INTEGER,
    "金額数値検査" DOUBLE PRECISION,
    "金額外観検査" DOUBLE PRECISION,
    "金額梱包" DOUBLE PRECISION,
    "金額洗浄" DOUBLE PRECISION,
    "金額二次作業" DOUBLE PRECISION,
    "稼働日数" INTEGER
);


CREATE TABLE "t_修正ログ" (
    "ID" BIGSERIAL,
    "日付" TIMESTAMP,
    "生産ロットID" VARCHAR(7),
    "項目" VARCHAR(5),
    "内容" VARCHAR(15)
);


CREATE TABLE "t_分割ロット" (
    "ID" BIGSERIAL,
    "元ロットID" VARCHAR(7),
    "新ロットID" VARCHAR(7),
    "元数量" INTEGER,
    "区分" VARCHAR(1),
    "作成日" TIMESTAMP
);


CREATE TABLE "t_工程マスタ" (
    "工程コード" VARCHAR(2),
    "工程名" VARCHAR(5)
);


CREATE TABLE "t_数量差異" (
    "ID" BIGSERIAL,
    "計量日" TIMESTAMP,
    "出荷日" TIMESTAMP,
    "号機" VARCHAR(4),
    "生産ロットID" VARCHAR(7),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "出荷数" INTEGER,
    "計量数" INTEGER,
    "差異" DOUBLE PRECISION
);


CREATE TABLE "t_現品票不具合内容" (
    "生産ロットID" VARCHAR(7),
    "不具合内容" VARCHAR(15),
    "処置内容" VARCHAR(15),
    "処置済" VARCHAR(1)
);


CREATE TABLE "t_現品票履歴" (
    "生産ロットID" VARCHAR(7),
    "号機" VARCHAR(5),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "客先" VARCHAR(30),
    "材質" VARCHAR(50),
    "材料ロットNO" VARCHAR(30),
    "機械担当者" VARCHAR(10),
    "営業担当者" VARCHAR(5),
    "数量" INTEGER,
    "現在工程名" VARCHAR(30),
    "現在工程コード" VARCHAR(2),
    "工程2" VARCHAR(30),
    "工程3" VARCHAR(30),
    "工程4" VARCHAR(30),
    "工程5" VARCHAR(30),
    "工程6" VARCHAR(30),
    "工程7" VARCHAR(30),
    "工程8" VARCHAR(30),
    "工程9" VARCHAR(30),
    "現在工程番号" INTEGER,
    "表面処理工程番号" INTEGER,
    "位置" VARCHAR(2),
    "品番ID" VARCHAR(6),
    "QRコード" VARCHAR(30),
    "備考" VARCHAR(30),
    "指示日" TIMESTAMP,
    "印刷日" TIMESTAMP,
    "完了日" TIMESTAMP,
    "発行フラグ" VARCHAR(1),
    "不適合品フラグ" VARCHAR(1),
    "不適合品数量" INTEGER,
    "処理済フラグ" VARCHAR(1),
    "完了フラグ" VARCHAR(1),
    "工程2備考" VARCHAR(20),
    "工程3備考" VARCHAR(20),
    "工程4備考" VARCHAR(20),
    "工程5備考" VARCHAR(20),
    "工程6備考" VARCHAR(20),
    "工程7備考" VARCHAR(20),
    "工程8備考" VARCHAR(20),
    "工程9備考" VARCHAR(20),
    "材料識別" INTEGER
);

