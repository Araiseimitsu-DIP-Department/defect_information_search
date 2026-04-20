# 不具合情報検索

不具合情報の検索、集計確認、Excel 出力を行う Windows 向けデスクトップアプリです。  
画面は `pywebview` + `Edge WebView2` で構成し、業務ロジックは既存の service / repository 層をそのまま使っています。

## 構成

```text
defect_information_search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ .env
├─ docs/
│  └─ 工業検査とエラー検出アイコン.png
└─ src/
   └─ defect_information_search/
      ├─ app.py
      ├─ config.py
      ├─ domain/
      ├─ infrastructure/
      ├─ services/
      └─ webview/
         ├─ app.py
         ├─ bridge.py
         └─ assets/
            ├─ index.html
            ├─ app.js
            └─ styles.css
```

## 起動フロー

1. `main.py` から `defect_information_search.app.main()` を呼びます。
2. `webview/app.py` が `.env` を読み込み、Access / PostgreSQL の接続先を決めます。
3. `pywebview` を `gui="edgechromium"` で起動し、Edge WebView2 上に画面を表示します。
4. 画面操作は `webview/bridge.py` 経由で service 層に渡り、検索・集計・Excel 出力を行います。

## 依存関係

`requirements.txt` に入っている主な依存は以下です。

- `pywebview`
- `pyodbc`
- `pandas`
- `openpyxl`
- `python-dotenv`
- `pyinstaller`

PySide6 / Qt 系は使用していません。

## 実行

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## ビルド

onefile の exe は次で作成します。

```powershell
.\build_exe.ps1
```

ビルドスクリプトは `docs\工業検査とエラー検出アイコン.png` から `.ico` を生成し、`.env` も同梱したうえで PyInstaller onefile を作成します。  
最終成果物は `dist\不具合情報検索.exe` のみです。

## 配布時の前提

- 配布先 PC には Microsoft Edge WebView2 Runtime が必要です。
- `.env` に設定した `ACCESS_DB_PATH` が到達可能である必要があります。
- 現在の `.env` はネットワーク共有上の Access DB を参照しています。

## アイコン

- 元画像: [`docs/工業検査とエラー検出アイコン.png`](docs/工業検査とエラー検出アイコン.png)
- ビルド時に `build/app_icon.ico` を生成し、exe のアイコンとアプリ内アイコンに使います。

## 現在の処理

- 品番候補検索
- 候補一覧からの詳細表示
- 号機絞り込み
- 集計値・不具合内訳表示
- 表示中データの Excel 出力
- 日付範囲での全品番エクスポート / 集計データ出力 / 廃棄データ出力

## 補足

- 旧 PySide6 画面は削除済みです。
- 画面の見た目と業務ロジックは維持し、UI だけを WebView 化しています。
