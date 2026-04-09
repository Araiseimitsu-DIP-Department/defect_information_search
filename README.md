# defect_information_search

Access の既存運用 DB を参照し、検索・集計表示・Excel エクスポートを行う Windows デスクトップアプリです。起動ファイルは `main.py` です。

## フォルダ構成

```text
defect_information_search/
├─ main.py                         # アプリ起動エントリポイント
├─ build_exe.ps1                   # onefile exe ビルドスクリプト
├─ requirements.txt                # Python 依存関係
├─ .env.example                    # 接続先設定例
├─ docs/                           # 受領仕様書・画面イメージ・VBA
└─ src/
   └─ defect_information_search/
      ├─ app.py                    # QApplication 初期化
      ├─ config.py                 # .env 読み込み
      ├─ models.py                 # 画面共通定義
      ├─ infrastructure/
      │  └─ access_gateway.py      # pyodbc 経由の Access 参照層
      ├─ services/
      │  ├─ defect_service.py      # 検索・集計・出力用データ取得
      │  └─ export_service.py      # Excel 保存と書式設定
      └─ ui/
         ├─ main_window.py         # メイン画面
         └─ table_models.py        # DataFrame 用テーブルモデル
      └─ ui_kit/
         ├─ theme.py               # Fusion + Palette + 共通 stylesheet
         ├─ assets/
         │  └─ combo_arrow_down.svg
         └─ widgets/
            ├─ modal_dialog.py
            ├─ message_box.py
            ├─ date_picker.py
            └─ busy_indicator.py
```

## セットアップ

1. `.env.example` をコピーして `.env` を作成します。
2. `.env` に親 Access DB のパスを設定します。

```env
ACCESS_DB_PATH=C:\Users\<USER>\Desktop\不具合情報検索.accdb
```

3. 仮想環境を作成し、依存関係をインストールします。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 起動

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## exe ビルド

```powershell
.\build_exe.ps1
```

生成物は `dist\defect_information_search.exe` です。

## 実装方針

- `.env` では親 DB の `不具合情報検索.accdb` のみを指定します。
- Python からは `pyodbc` で親 DB を参照します。
- リンクテーブルは親 DB 側の定義をそのまま使います。
- 既存 VBA の SQL を踏襲し、以下を実装しています。
  - 品番検索
  - 品番別の不具合集計
  - 号機絞り込み
  - 明細一覧表示
  - 検索結果の Excel 出力
  - 期間指定の不具合情報出力
  - 集計データ出力
  - 廃棄データ出力

## 注意

- 実行環境は Windows 固定です。
- Access のリンク先 DB や権限状況によっては、参照時に Access 側エラーが返る場合があります。
- このリポジトリ側では実 DB への完全な動作確認までは行っていません。`.env` 設定後に実環境で接続確認してください。
