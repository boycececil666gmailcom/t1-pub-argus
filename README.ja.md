# Argus

**README の言語：** [English](README.md) · 日本語 · [中文](README.zh.md)

> *ギリシャ神話の百眼の巨人アルゴス・パノプテスにちなんで命名。眠らず、すべてを見守り続けた。*
>
> *いた简单な一句话から始まった六个月个人プロジェクト：私の時間は何処へ向かっているのか？*

5 秒ごとにアクティブなアプリとウィンドウを静かに記録する Python ツールです。バックグラウンドで動かしながら、ライブダッシュボードやターミナルレポートで自分の時間の使い方を把握できます。

## Screenshots

スクリーンショットは [English README](README.md#screenshots) を参照してください。

---

## Origin Story — 開発のきっかけ

六个月前のことです。

僕はちょうど —— フルタイムの仕事、フリーランスの案件、勉学 —— という過密な时期を終えたばかりでした。ある夜、自分に简单な质問を投げかけました：**自分の時間は实际どこに行っているのか？**

記録试着想了想。数えてみた。うまくいかない。問題は努力ではなかった —— 見えないことこそが问题だった。改善しようにも測定できなければ、コンピュータでの作业時間を後から振り返ることはできない。

そこで Argus を作りました。

タスク管理ツールでも、ポモドーロタイマーでもありません。**受动的で、常时稼働する镜**として、自分のしていることをただ記録し、後から真実を見られるようにしました。5秒ごとに、プロンプトなし、摩擦なしで。

### なぜ自作したのか？

既存のツールを検討しました：RescueTime、ActivityWatch、Toggl。どれも很不错ですが、それぞれに僕が求めたくないものがありました：

- クラウド依存 —— すべてのウィンドウ活動をサーバーに送るのが気が進まなかった
- サブスクリプション料金 —— 永久に動かし続けたいものに
- Linuxのギャップ —— 大半が第一級サポートを提供していなかった
- TUIがない —— 僕はターミナルで暮らしている

Argusは僕が欲しいと思ったツールです：**ローカル専用、クロスプラットフォーム、ゼロコスト、ターミナルネイティブ。** Windows、macOS、Linuxのいずれでもバックグラウンドで静かに動きます。データは決してあなたの機械から離れません。TUIダッシュボードはTextualで駆動され、リアルタイムで更新されます。週次レポートは今否则気づかないパターンを浮かび上がらせます。

### 开发から习ったこと

过半年のソロ開発は予期しない教训をもたらしました：**制约こそが机能だった。** 早朝や週末の隙間時間を 利用してArgusを構築 inúmer ので。过酷な设计はできませんでした。すべての决定に正当化が必要。シンプルさは妥协ではなく哲学になりました。

结果是。每天使うようになりました。そして今、OSSです。

> 自分の時間がどこに行っているのか気になったことがあるなら —— [試してみてください](https://github.com/boycececil666/t1-pub-argus)。

---

## 設計の視点

Argus の設計は段階的なプロセスに従っています：

```
機能設計 → 要件定義 → 基本設計 → 詳細設計
```

---

### 機能設計

機能は二つの軸に分類されます：**機能的要件**（何をするか）と**非機能的要件 / 品質属性**（どの程度 잘 하는지）。

#### 機能的要件

| # | 要件 | 根拠 |
|---|---|---|
| F1 | フォアグラウンドウィンドウを追跡 | コアバリュー — 常駐、静音、バックグラウンド |
| F2 | アプリを自動分類 | 生プロセス名を意味あるカテゴリに変換 |
| F3 | スナップショットを SQLite に保存 | シンプル、移植性ゼロ設定、サーバー不要 |
| F4 | TUI プロセス内にトラッカーを内包 | `argus tui` 一発で起動、バックグラウンドサービス不要 |
| F5 | ログイン時に自動起動 | ユーザー行動ゼロで記録開始 |
| F6 | 6言語対応 TUI | 非英語話者へのアクセシビリティ |
| F7 | 12 色のテーマ | コード変更なしでパーソナライズ |

#### 非機能的要件（品質属性）

| # | 品質 | 目標 | 動機 |
|---|---|---|---|
| NF1 | **プライバシー** — 全データローカル保存 | ネットワーク、クラウド、テレメトリなし | ユーザー信頼 |
| NF2 | **可用性** — クロスプラットフォーム | Windows、macOS、Linux | プラットフォーム多様性 |
| NF3 | **パフォーマンス** — 軽量 | 一般的なデスクトップで CPU 1% 未満 | 常駐制約 |
| NF4 | **可用性** — アイドル検出 | ユーザーが離れている間のスナップショットをスキップ | データ品質 |
| NF5 | **パフォーマンス** — 低ストレージオーバーヘッド | 5 秒間隔で 1 行 | 長期運用 가능성 |
| NF6 | **保守性** — モジュラー設計 | 明確なレイヤー分離 | 拡張性 |

---

### 要件定義

上の機能表から直接導出。

| 要件 | 参照元 | 目標 |
|---|---|---|
| フォアグラウンドウィンドウを追跡 | F1 | 5 秒間隔で常駐記録 |
| アイドルを検出してスキップ | F1 + NF4 | 離席時間をレポートから除外 |
| アプリを自動分類 | F2 | 11 の組み込みカテゴリ |
| スナップショットをローカルに保存 | F3 | `~/.argus/` 内の SQLite |
| TUI 内にトラッカーを内包 | F4 | バックグラウンドサービスなし |
| ログイン時に自動起動 | F5 | OS 別の登録 |
| 多言語 UI | F6 | 6 言語、設定に保存 |
| 12 色のテーマ | F7 | `T` で切り替え |
| ローカルのみ、ネットワークなし | NF1 | プライバシー保証 |
| クロスプラットフォーム | NF2 | Win / macOS / Linux |
| CPU 1% 未満 | NF3 | 一般的なデスクトップハードウェア |
| モジュラー / 拡張可能 | NF6 | レイヤーとモジュールの分離 |

### 基本設計 — 三層構造

```
┌──────────────────────────────────────────────┐
│  UI 層: TUI (Textual) + レポート (Rich)      │
├──────────────────────────────────────────────┤
│  サービス層: トラッカー、ストレージ、レポート  │
├──────────────────────────────────────────────┤
│  プラットフォーム層: Win32 / macOS / Linux   │
└──────────────────────────────────────────────┘
```

### 詳細設計 — モジュールの役割

| モジュール | 責務 |
|---|---|
| `tracker.py` | プラットフォーム別のウィンドウ検出＋アイドル検出 |
| `storage.py` | SQLite 初期化、`record()` 書込、`query_range()` 読込 |
| `daemon.py` | フォアグラウンドポーリングループ（`start` コマンド） |
| `tui.py` | Textual ダッシュボード＋組み込みバックグラウンドポーラー |
| `report.py` | 日次・週次 Rich レポート＋ステータスパネル |
| `autostart.py` | OS 別のログイン項目登録 |
| `config.py` | 定数、カテゴリマップ、設定の永続化 |
| `i18n.py` | UI 文字列カタログ（6 言語） |

---

## Architecture diagrams

The following [Mermaid](https://mermaid.js.org/) blocks render natively on GitHub. They document the module structure, key types, the tracking polling loop, and the `report` command call sequence.

### Sequence diagram — `report`

```mermaid
sequenceDiagram
    actor User
    participant CLI as main.py
    participant Report as report.py
    participant Storage as storage.py
    participant Rich as Rich console
    User->>CLI: report optional date
    CLI->>Report: daily_report(datetime)
    Report->>Storage: query_range(start, end)
    Storage-->>Report: snapshot rows
    Report->>Report: aggregate and categorise
    Report->>Rich: tables and panels
    Rich-->>User: terminal output
```

### Module structure

High-level dependency flow: `main.py` delegates to each `argus/` module.

```mermaid
flowchart LR
    subgraph entry[Entry]
        main[main.py]
    end
    subgraph pkg[argus package]
        config[config.py]
        tracker[tracker.py]
        storage[storage.py]
        daemon[daemon.py]
        report[report.py]
        tui[tui.py]
        autostart[autostart.py]
        i18n[i18n.py]
    end
    main --> daemon
    main --> report
    main --> tui
    main --> autostart
    main --> tracker
    daemon --> tracker
    daemon --> storage
    daemon --> config
    tui --> tracker
    tui --> storage
    tui --> config
    tui --> report
    tui --> autostart
    tui --> i18n
    report --> storage
    report --> config
    autostart --> config
    storage --> config
```

### Class diagram

`WindowInfo` is the TypedDict snapshot shape returned by the tracker; TUI screens subclass Textual widgets.

```mermaid
classDiagram
    direction TB
    class App
    class Static
    class ModalScreen
    App <|-- ArgusApp
    Static <|-- StatusWidget
    ModalScreen <|-- HelpScreen
    ModalScreen <|-- WelcomeScreen
    class WindowInfo {
        <<TypedDict>>
        app_name
        window_title
        exe_path
    }
    note for App "textual.app.App"
    note for Static "textual.widgets.Static"
    note for ModalScreen "textual.screen.ModalScreen"
```

### Activity diagram — tracking loop

Shared logic for the `start` / daemon and the TUI background poller: poll interval → idle check → record snapshot → wait → repeat.

```mermaid
flowchart TD
    A([Start tracker]) --> B[init_db]
    B --> C{Still running?}
    C -->|yes| D[get_idle_seconds]
    D --> E[get_active_window]
    E --> F{Foreground window known?}
    F -->|yes| G[record snapshot]
    F -->|no| H[Skip write]
    G --> I[Wait POLL_INTERVAL]
    H --> I
    I --> C
    C -->|no / interrupt| J([Stop])
```

---

## 技術スタック

| 機能 | ツール |
|---|---|
| アクティブウィンドウ検出 | `pywin32`（Windows）· `osascript`（macOS）· `xdotool`（Linux）|
| アイドル検出 | `GetLastInputInfo` via ctypes（Windows）· `ioreg`（macOS）· `xprintidle`（Linux）|
| プロセス情報 | `psutil` |
| ストレージ | SQLite（標準ライブラリ `sqlite3`）|
| CLI | `Typer` |
| ターミナルレポート | `Rich` |
| インタラクティブダッシュボード | `Textual` |
| 自動起動 | レジストリキー（Windows）· LaunchAgent plist（macOS）· XDG autostart（Linux）|

---

## 開発環境のセットアップ

```bash
pip install -r requirements.txt
```

**Linux のみ** — ウィンドウ・アイドル検出に必要なシステムパッケージ：
```bash
sudo apt install xdotool xprintidle   # Ubuntu / Debian
sudo dnf install xdotool xprintidle   # Fedora
```

---

## スタンドアロン実行ファイルのビルド

Python や pip を一切インストールせずに使える単一ファイルにパッケージングします。

```bash
# ビルドツールのインストール（初回のみ）
pip install -r requirements-dev.txt

# ビルド
python build.py
```

出力は `dist/` ディレクトリに：

| プラットフォーム | ファイル |
|---|---|
| Windows | `dist/argus.exe` |
| Linux | `dist/argus` |
| macOS | `dist/argus` |

実行ファイルは完全に自己完結しています。Python・Textual・Rich などすべての依存関係を内包。**ユーザーは何もインストール不要です。**

> **Linux の注意：** `xdotool` と `xprintidle` はシステムパッケージのためバンドルできません。Linux 版を配布する際は以下を案内してください：
> ```bash
> sudo apt install xdotool xprintidle
> ```

---

## 使い方（ソースから実行）

```bash
# インタラクティブダッシュボード（推奨——バックグラウンドでトラッカーも起動）
python src/main.py tui

# トラッカーのみフォアグラウンドで起動（Ctrl+C で停止）
python src/main.py start

# 今日のアクティビティレポート
python src/main.py report

# 指定日のレポート
python src/main.py report --date 2026-03-15

# 今週のレポート
python src/main.py week

# 今何をしているか確認
python src/main.py status

# ログイン時の自動起動を登録
python src/main.py install

# 自動起動の登録解除
python src/main.py uninstall
```

### ビルド済み実行ファイルの使い方

```bash
argus tui
argus report
argus install
# 同じコマンド — "python src/main.py" プレフィックス不要
```

---

## TUI ダッシュボード

`argus tui` を実行すると [Textual](https://textual.textualize.io/) による全画面リアルタイムダッシュボードが開きます。トラッカーもバックグラウンドで同時起動するため、別途 `start` は不要です。

**表示内容**

- **ステータスパネル** — アクティブなアプリ・カテゴリ・ウィンドウタイトル・アイドル時間・スナップショット総数
- **今日** — 上位 10 アプリとカテゴリ内訳（プログレスバー付き）。◀ ▶ と「今日」で別の日へ
- **今週** — 日別サマリー・週次カテゴリ分布・週次上位アプリ。◀ ▶ と「今週」で別の週へ

5 秒ごとに自動更新されます。「今日」「今週」表示中は実カレンダーに追従（日付変更後も今日・今週のまま）。

**キーボードショートカット**

| キー | 動作 |
|---|---|
| `?` | ヘルプ画面 |
| `R` | 全データを今すぐ更新 |
| `T` | カラーテーマを切り替え |
| `L` | 表示言語を切り替え |
| `A` | 自動起動の切り替え（有効 / 無効）|
| `O` | データフォルダをファイルマネージャーで開く |
| `[` `]` | 前日 / 翌日（ダッシュボード履歴） |
| `{` `}` | 前週 / 翌週（ダッシュボード履歴） |
| `Q` | 終了 |

**ツールバーボタン**

| ボタン | 動作 |
|---|---|
| `自動起動  ON/OFF` | ログイン自動起動の切り替え |
| `JA  日本語` | 言語の切り替え |
| `DBフォルダを開く` | データフォルダを開く |

---

## 言語サポート

TUI は 6 言語に対応しており、`L` で順番に切り替えられます：

| コード | 言語 |
|---|---|
| `en` | English |
| `ja` | 日本語 |
| `zh` | 中文 |
| `fr` | Français |
| `de` | Deutsch |
| `es` | Español |

言語の選択は `~/.argus/settings.json` に保存され、次回起動時に復元されます。

---

## テーマ

TUI で `T` を押すと 12 種類の内蔵 Textual テーマを順番に切り替えられます（追加インストール不要）：

`textual-dark` · `textual-light` · `nord` · `gruvbox` · `catppuccin-mocha` · `catppuccin-latte` · `dracula` · `tokyo-night` · `monokai` · `solarized-dark` · `solarized-light` · `flexoki`

テーマの選択も自動的に保存・復元されます。

---

## データ

すべてのデータは `~/.argus/argus.db`（SQLite）に保存されます（フォルダは環境変数 `ARGUS_DATA` で変更可）。5 秒ごとのスナップショットが 1 行：

| カラム | 型 | 説明 |
|---|---|---|
| `ts` | REAL | Unix タイムスタンプ |
| `app_name` | TEXT | プロセス名（例：`chrome`、`code`）|
| `window_title` | TEXT | その時点のウィンドウタイトル |
| `exe_path` | TEXT | 実行ファイルのフルパス |
| `idle` | INTEGER | アイドルしきい値を超えた場合 1 |

アイドルのスナップショットはレポートと TUI でデフォルト除外されます。

ユーザー設定（言語、テーマ）は `~/.argus/settings.json` に別途保存されます。

---

## カテゴリ

アプリは自動的に以下のカテゴリに分類されます：

`ブラウザ` · `IDE / エディタ` · `ターミナル` · `コミュニケーション` · `デザイン` · `ゲーム` · `生産性` · `メディア` · `ファイルマネージャー` · `システム` · `その他`

マッピングを変更するには `src/argus/config.py` の `CATEGORIES` 辞書を編集してください。

---

## 設定調整

`src/argus/config.py` 上部の 2 つの定数を編集：

```python
POLL_INTERVAL  = 5    # スナップショットの間隔（秒）
IDLE_THRESHOLD = 60   # アイドルとみなす無操作時間（秒）
```

---

## プロジェクト構成

```
src/
├── main.py               # Typer CLI エントリポイント
└── argus/
    ├── __init__.py       # パッケージバージョン
    ├── config.py         # 定数・カテゴリマップ・設定永続化
    ├── i18n.py           # UI 文字列カタログ（6 言語）
    ├── tracker.py        # アクティブウィンドウ + アイドル検出
    ├── storage.py        # SQLite 読み書き
    ├── daemon.py         # フォアグラウンドポーリングループ
    ├── report.py         # Rich 日次 / 週次 / ステータスレポート
    ├── tui.py            # Textual リアルタイムダッシュボード
    └── autostart.py      # 自動起動ヘルパー（Win / macOS / Linux）
build.py                  # PyInstaller ビルドスクリプト → dist/argus[.exe]
requirements.txt          # ランタイム依存関係
requirements-dev.txt     # ランタイム + ビルドツール（pyinstaller）
dist/                    # コンパイル済み実行ファイル（.gitignore 済み）
```
