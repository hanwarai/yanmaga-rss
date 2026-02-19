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

テストは存在しません。ローカル実行で動作確認してください。

## Architecture

### データフロー

1. `feed.csv` を読み込む（形式: `id,URLエンコードされたマンガタイトル`）
2. 各エントリに対して `https://yanmaga.jp/comics/{title}` にリクエスト
3. BeautifulSoup で HTML をパース → 無料エピソード (`mod-episode-point--free`) を抽出
4. `feedgenerator` で Atom フィードを生成 → `feeds/{id}.xml` に書き出し
5. Jinja2 で `templates/index.html` をレンダリング → `feeds/index.html` に書き出し

### 主要ファイル

| ファイル | 役割 |
|---|---|
| `main.py` | 唯一の実行スクリプト。スクレイピング・フィード生成・HTML生成をすべて担う |
| `feed.csv` | 購読対象マンガの定義。`id,URLエンコードタイトル` の CSV |
| `templates/index.html` | Jinja2 テンプレート。`feeds` 変数（`id`, `title` を持つオブジェクトのリスト）を受け取る |
| `feeds/` | 出力ディレクトリ。`.gitignore` 対象。GitHub Pages にデプロイされる |

### マンガの追加方法

`feed.csv` に新しい行を追加する:

```
{id},{URLエンコードされたマンガタイトル}
```

`id` はフィード XML のファイル名になる（例: `fable_2nd` → `feeds/fable_2nd.xml`）。
タイトルは yanmaga.jp の URL パス部分をそのまま使用する（例: `https://yanmaga.jp/comics/アンダーニンジャ` → `%E3%82%A2%E3%83%B3%E3%83%80%E3%83%BC%E3%83%8B%E3%83%B3%E3%82%B8%E3%83%A3`）。

### CI/CD

GitHub Actions (`.github/workflows/gh-pages.yaml`) が以下のタイミングで自動実行:
- `main` ブランチへの push
- 12 時間ごと（cron）

`feeds/` ディレクトリの内容が GitHub Pages にデプロイされ、フィードは `https://hanwarai.github.io/yanmaga-rss/{id}.xml` で公開される。
