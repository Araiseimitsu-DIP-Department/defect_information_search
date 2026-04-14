# 業務アプリ共通アーキテクチャ

この文書は、Access ベース業務アプリをデスクトップ化し、将来 PostgreSQL に移行しても破綻しないための実装基準です。

## 1. アーキテクチャ方針

最小構成で動かしつつ、責務分離は明確にします。

- `presentation`
  - PySide6 の画面、入力、表示、ダイアログ
- `application`
  - ユースケース、画面から呼ぶ処理の流れ
- `domain`
  - 業務モデル、値オブジェクト、業務ルール
- `infrastructure`
  - Access / PostgreSQL / 外部 I/O
- `shared`
  - 例外、型変換、日時ユーティリティ、共通定数

UI から SQL は直接書きません。接続も `infrastructure` に閉じ込めます。

## 2. フォルダ構成

```text
src/defect_information_search/
  presentation/
    main_window.py
    table_models.py
    dialogs/
  application/
    use_cases/
      search_defects.py
      export_defects.py
    ports/
      defect_repository.py
  domain/
    models/
      defect_record.py
      staff.py
      inventory.py
    value_objects/
      defect_id.py
      machine_id.py
      business_date.py
  infrastructure/
    access/
      connection.py
      defect_repository.py
    postgres/
      defect_repository.py
    mappers/
      defect_row_mapper.py
  shared/
    errors.py
    logging.py
    type_conversion.py
    constants.py
```

現状の `services` は、移行時に `application` へ整理すると分かりやすいです。

## 3. ドメインモデル

業務概念でモデルを作ります。テーブル名に引っ張られません。

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DefectRecord:
    lot_id: str
    part_number: str
    defect_date: date
    machine_code: str | None
    defect_type: str | None
    defect_count: int
    quantity: int

    @property
    def defect_rate(self) -> float | None:
        if self.quantity == 0:
            return None
        return self.defect_count / self.quantity
```

値として切り出しやすいものは、必要になった段階で分離します。

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class DefectId:
    value: int


@dataclass(frozen=True)
class BusinessDate:
    value: date
```

## 4. Repository interface

DB 実装は差し替え可能にします。

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Protocol

from defect_information_search.domain.models.defect_record import DefectRecord


class DefectRepository(Protocol):
    def find_products(self, keyword: str) -> list[dict[str, object]]: ...
    def find_defects(
        self,
        part_number: str,
        date_from: date,
        date_to: date,
    ) -> list[DefectRecord]: ...
    def find_defects_between(
        self,
        date_from: date,
        date_to: date,
    ) -> list[DefectRecord]: ...
```

`Protocol` を使うと、Access / PostgreSQL どちらでも同じ扱いにできます。

## 5. Access 実装例

Access のクセは `infrastructure` 内で吸収します。

```python
from datetime import date

from defect_information_search.application.ports.defect_repository import DefectRepository
from defect_information_search.domain.models.defect_record import DefectRecord
from defect_information_search.infrastructure.access.connection import AccessConnection


class AccessDefectRepository:
    def __init__(self, connection: AccessConnection) -> None:
        self._connection = connection

    def find_defects(self, part_number: str, date_from: date, date_to: date) -> list[DefectRecord]:
        sql = """
            SELECT [part_number], [defect_date], [machine_code], [defect_count], [quantity]
            FROM [defect_records]
            WHERE [part_number] = ?
              AND [defect_date] BETWEEN ? AND ?
        """
        rows = self._connection.fetch_all(sql, [part_number, date_from, date_to])
        return [
            DefectRecord(
                lot_id=str(row["lot_id"]),
                part_number=str(row["part_number"]),
                defect_date=row["defect_date"],
                machine_code=row["machine_code"],
                defect_type=row.get("defect_type"),
                defect_count=int(row["defect_count"] or 0),
                quantity=int(row["quantity"] or 0),
            )
            for row in rows
        ]
```

Access 依存の補正はここでまとめます。

- `NULL` を Python 側で補正する
- `COUNTER` は主キー候補として扱う
- 型が曖昧な列は変換する
- FK が無い前提で整合性を補う

## 6. ユースケース例

画面はユースケースを呼ぶだけにします。

```python
from dataclasses import dataclass
from datetime import date

from defect_information_search.application.ports.defect_repository import DefectRepository


@dataclass(frozen=True)
class SearchDefectsResult:
    items: list[object]
    summary: dict[str, object]


class SearchDefectsUseCase:
    def __init__(self, repository: DefectRepository) -> None:
        self._repository = repository

    def execute(self, part_number: str, date_from: date, date_to: date) -> SearchDefectsResult:
        defects = self._repository.find_defects(part_number, date_from, date_to)
        quantity = sum(record.quantity for record in defects)
        defect_count = sum(record.defect_count for record in defects)
        return SearchDefectsResult(
            items=defects,
            summary={
                "quantity": quantity,
                "defect_count": defect_count,
                "defect_rate": (defect_count / quantity) if quantity else None,
            },
        )
```

## 7. UI 呼び出し例

PySide6 画面は、取得結果を表示するだけにします。

```python
from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    def __init__(self, search_use_case) -> None:
        super().__init__()
        self._search_use_case = search_use_case

    def on_search_clicked(self) -> None:
        result = self._search_use_case.execute(
            self.part_number_edit.text().strip(),
            self.date_from_edit.date().toPython(),
            self.date_to_edit.date().toPython(),
        )
        self.summary_label.setText(str(result.summary["defect_count"]))
```

## 8. エラー処理設計

エラーは「ユーザー表示」と「ログ」を分けます。

- DB 接続失敗
  - ユーザー表示: 「データベースに接続できません」
  - ログ: 接続文字列、例外型、スタックトレース
- NAS 未接続
  - ユーザー表示: 「共有フォルダに接続できません」
  - ログ: パス、OS エラー
- ODBC エラー
  - ユーザー表示: 「データ取得に失敗しました」
  - ログ: SQL 実行時の詳細
- データ不整合
  - ユーザー表示: 「一部データが不正です」
  - ログ: どの列で失敗したか
- 型変換エラー
  - ユーザー表示: 「日付または数値の形式が不正です」
  - ログ: 元値と対象列

```python
class AppError(Exception):
    pass


class RepositoryError(AppError):
    pass


class DataConversionError(AppError):
    pass
```

UI 側では例外を丸ごと表示せず、メッセージ変換を通します。

## 9. PostgreSQL 移行時の差し替えポイント

差し替える場所を最初から固定します。

- `AccessDefectRepository` を `PostgresDefectRepository` に差し替える
- SQL 方言を `infrastructure` に閉じ込める
- 列名と Python 属性名の対応を `mapper` に分離する
- `COUNTER` 相当は `BIGSERIAL` または `IDENTITY` に置き換える
- `VARCHAR` 多用列は `boolean` / `enum` / `date` / `numeric` に正規化する
- インデックスはユースケース起点で設計する

## 10. 実装ルール

- Python 3.10+ を前提にする
- モデルは `dataclass` を基本にする
- UI で SQL を書かない
- DB 接続を複数箇所に散らさない
- Access 仕様をアプリ層に漏らさない
- まずは最小構成で動かし、必要なところだけ拡張する

## 11. 既存プロジェクトへの当てはめ

このリポジトリでは、当面は次の対応で十分です。

- `ui` は `presentation` 相当
- `services` は `application` 相当
- `infrastructure/access_gateway.py` は Access 接続の基盤
- `models.py` の共通定義は将来的に `shared` へ移動

大改修を一気にやるより、まず repository interface を導入して、UI から DB 直結をなくすのが最優先です。
