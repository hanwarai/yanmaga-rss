# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

yanmaga-rss は、[ヤングマガジン公式サイト (yanmaga.jp)](https://yanmaga.jp) の無料公開エピソードを Atom フィード形式で配信する Python スクリプトです。生成されたフィードは GitHub Pages でホスティングされます。

## Commands

```bash
# 依存関係のインストール
uv sync --all-extras

# メインスクリプトの実行（フィード生成）
uv run main.py
```

ユニットテストは存在しない。ローカル実行で動作確認する。PR には build ジョブ（依存の整合性チェックと yanmaga.jp への実疎通）が CI として走る。

Python は `pyproject.toml` で `>=3.13` を要求し、`.python-version` も `3.13` にピン留め。CI では `actions/setup-python` が `python-version-file: pyproject.toml` を読んで `requires-python` を解決する。

## Architecture

### データフロー

1. `feed.csv` を読み込む（形式: `id,URLエンコードされたマンガタイトル`）
2. `id` を `^[A-Za-z0-9_-]+$` で検証し、不正な行はスキップ（出力パス経由の path traversal 防止）
3. 各エントリに対して `https://yanmaga.jp/comics/{title}` にリクエスト
4. BeautifulSoup で HTML をパース:
   - `div.detailv2-thumbnail-image img` からフィードタイトル (`alt`) とカバー画像 (`src`) を取得。取れなければその id はスキップ
   - `div.mod-episode-public` を走査し、内部に `span.mod-episode-point--free` を持つエピソードのみ採用
5. `feedgenerator.Atom1Feed` で Atom フィードを生成 → `feeds/{id}.xml` に書き出し
6. Jinja2 (`autoescape=True`) で `templates/index.html` をレンダリング → `feeds/index.html` に書き出し

### 主要ファイル

| ファイル | 役割 |
|---|---|
| `main.py` | 唯一の実行スクリプト。スクレイピング・フィード生成・HTML生成をすべて担う |
| `feed.csv` | 購読対象マンガの定義。`id,URLエンコードタイトル` の CSV |
| `templates/index.html` | Jinja2 テンプレート。`feeds` 変数（`id`, `title` を持つオブジェクトのリスト）を受け取る |
| `feeds/` | 出力ディレクトリ。`.gitkeep` 以外は ignore (`/feeds/*.xml`, `/feeds/index.html`)。GitHub Pages にデプロイされる |

### 生成 HTML の挙動

`feeds/index.html` は購読用のランディングページ。各マンガ行にある `/feed subscribe` ボタンは、`https://hanwarai.github.io/yanmaga-rss/{id}.xml` を前置した Misskey 形式のコマンド文字列をクリップボードへコピーする。ユーザーがチャットに貼り付けて購読する想定。

### マンガの追加方法

`feed.csv` に新しい行を追加する:

```
{id},{URLエンコードされたマンガタイトル}
```

`id` はフィード XML のファイル名になる（例: `fable_2nd` → `feeds/fable_2nd.xml`）。
タイトルは yanmaga.jp の URL パス部分をそのまま使用する（例: `https://yanmaga.jp/comics/アンダーニンジャ` → `%E3%82%A2%E3%83%B3%E3%83%80%E3%83%BC%E3%83%8B%E3%83%B3%E3%82%B8%E3%83%A3`）。

### CI/CD

姉妹 RSS リポジトリと同じ 2 ワークフロー構成:

**`ci.yaml`** — PR ゲート:
- トリガー: `pull_request`。ジョブ名は `check`（main の branch protection がこの名前を必須チェックにしているので、**変えると必須チェックが報告されなくなる**）
- 処理: `uv sync --locked --all-extras` → actionlint → smoke test（`python -c "import main"`）
- **実フェッチ（`uv run main.py`）は含めない**。PR を yanmaga.jp の可用性に依存させないため。スクレイピングの疎通は push と schedule 実行が担う
- `--locked` は `uv.lock` と `pyproject.toml` の整合性を検証する。外すと lock が壊れた Dependabot PR でも暗黙に再解決されて green になるため外さないこと

**`gh-pages.yaml`** — 公開:
- トリガー: `main` への push、12 時間ごとの cron、`workflow_dispatch`
- 処理: `uv sync --locked --all-extras` → `uv run main.py` → `feeds/` を GitHub Pages にデプロイ
- フィードは `https://hanwarai.github.io/yanmaga-rss/{id}.xml` で公開される

**`dependabot-auto-merge.yaml`** — non-major の Dependabot PR を自動マージ（major は手動レビューに残す）。

uv ピンの読み取りは `.github/scripts/resolve-uv-version.sh` に切り出して両ワークフローで共有する（`grep -P` は GNU 限定で macOS では動かないため POSIX sed で実装）。一方 `uses:` の行は両ファイルに重複させたままにすること — Dependabot の github-actions エコシステムは `.github/workflows/` とルートの `action.yml` しか走査せず、composite action へ切り出すとバージョン追跡から外れる（dependabot-core#9788）。
