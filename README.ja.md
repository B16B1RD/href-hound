# href-hound（リンクチェッカー）

本プロジェクトは Vibe Coding（OpenAI Codex）を使用して作成されました。

href-hound は、起点 URL から静的 HTML ページをクロールし、リンク切れを検出する Python 製ツールです。コマンドラインインターフェース（CLI）と PyQt5 ベースのグラフィカルユーザインタフェース（GUI）を備え、共通のコアロジックを使用しています。

## 機能

- HTML ページをクロールし、`<a>` タグのリンクを抽出
- オプションでリソースリンクもチェック（`<img>`, `<link>`, `<script>`）
- 各種オプション設定が可能
  - 同一オリジンのみ / サブドメインを含む
  - 最大クロール深度（`-1` で無制限）
  - 除外/包含 URL パターン（部分文字列マッチ、複数指定可）
  - User-Agent, タイムアウト, 同時リクエスト数, リクエスト間隔, エラー判定ステータスコード
- 壊れたリンクをソースページごとにまとめた単一ファイルの HTML レポートを生成
- CLI と GUI は同一のコアロジックを共有

## 必要要件

- Python 3.7 以上
- PyQt5
- その他の依存ライブラリは `requirements.txt` に記載

依存ライブラリのインストール:
```bash
pip install -r requirements.txt
```

## インストール

```bash
git clone <リポジトリURL>
cd <リポジトリディレクトリ>
pip install -r requirements.txt
```

## CLI の使い方

CLI チェッカーを実行:
```bash
python -m href_hound.cli <start_url> [オプション]
```

主なオプション:
- `-o, --output`: 出力 HTML レポートのファイルパス（デフォルト: `report.html`）
- `--same-origin`: 同一オリジンのみクロール（デフォルト）
- `--include-subdomains`: サブドメインを含める
- `--max-depth N`: 最大クロール深度（デフォルト: 3、`-1` で無制限）
- `--exclude PATTERN`: URL に PATTERN を含む場合は除外（部分文字列マッチ、複数指定可）
- `--include PATTERN`: URL に PATTERN を含む場合のみ対象（部分文字列マッチ、複数指定可）
- `--check-resources`: リソースリンク（`img`, `link`, `script`）もチェック
    - `--user-agent STRING`: User-Agent ヘッダ（デフォルト: `href-hound/1.0`）
- `--timeout SECONDS`: タイムアウト秒数（デフォルト: `10.0`）
- `--concurrency N`: 同時リクエスト数（デフォルト: `5`）
- `--delay SECONDS`: リクエスト間隔（秒）（デフォルト: `0.0`）
- `--error-codes CODE1,CODE2,...`: リンク切れと見なす HTTP ステータスコードをカンマ区切りで指定

例:
```bash
python -m href_hound.cli https://example.com -o report.html \
  --max-depth -1 --check-resources \
  --exclude "/blocks/docs/en/" \
  --user-agent "MyBot/1.0" --timeout 5
```

## GUI の使い方

GUI アプリケーションを実行:
```bash
python -m href_hound.gui
```

GUI 上で:
1. 「起点 URL」と「出力レポート」のファイルパスを入力
2. オプションを設定:
   - 同一オリジン / サブドメインの有無
   - 最大深度（`-1` で無制限）
   - 除外/包含 URL パターン（1行に1つずつ入力、複数可）
   - リソースリンクチェックの有無
   - User-Agent, タイムアウト, 同時リクエスト数, リクエスト間隔, エラーコード
3. 「開始」ボタンで実行。進捗状況とログがリアルタイム表示
4. 実行中に「中断」ボタンで停止
5. 完了後に「レポートを開く」ボタンで HTML レポートを表示

## レポート形式

生成される HTML レポートは、壊れたリンクをソースページごとにグループ化し、リンク先 URL、ステータスコード、エラーメッセージ（あれば）を一覧表示します。

## トラブルシューティング

- Ubuntu on WSL2 環境で GUI の日本語が文字化けする場合は、日本語フォントをインストールしてください:
  ```bash
  sudo apt update && sudo apt install fonts-noto-cjk
  ```

---
href-hound で効率的にリンク切れチェックを行いましょう!