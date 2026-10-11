# ポートフォリオサイト

Pythonによる定型業務自動化サービスを紹介する、1ページの静的サイトです。
素の HTML と CSS だけで作っており、ビルド作業や外部ライブラリは必要ありません。JavaScript も使っていません。

## ファイル構成

```
portfolio/
├── index.html              サイト本体（Hero / About / Projects / Service / Contact）
├── css/style.css           デザイン（配色は冒頭の :root で変更できます）
├── assets/favicon.svg      ブラウザのタブに表示されるアイコン
├── demo/sales-cleanup/     公開用デモ（Pythonスクリプト、架空データ、説明）
├── .nojekyll               GitHub Pages でファイルをそのまま配信するための空ファイル
└── README.md               このファイル
```

## ローカルでの確認方法

`index.html` をブラウザで直接開いても表示できます。
公開時と同じ条件で確認する場合は、このフォルダで簡易サーバーを起動します。

```bash
cd portfolio
python -m http.server 8000
```

ブラウザで <http://localhost:8000> を開きます。終了するときは `Ctrl + C` を押します。
スマートフォン表示は、ブラウザの開発者ツール（F12）のデバイス表示で確認できます。

## 公開前の確認項目

| 項目 | 現在の状態 | 編集する場所 |
|---|---|---|
| 表示名 | 「ユリィ」 | `index.html`（タイトル、ヘッダー、About、フッターの4か所） |
| 出品ページのURL | 設定済み | `index.html` の `出品ページURL` というコメントの直下（Service と Contact の2か所） |
| 対応できる業務の例／情報収集の範囲／対象外 | 制作時に作成した文章 | `index.html` の Service。出品ページの記載と合っているか確認 |
| 「仕事への姿勢」の文章 | 制作時に作成した文章 | `index.html` の About |
| Power BI の公開用デモ | 「準備中」と表示 | `index.html` の Projects |

出品ページのURLを変更するときは、`index.html` を `skill.libecity.com` で検索し、2か所とも書き換えてください。
HTML内では、URLに含まれる `&` を `&amp;` と書きます。

### 掲載内容のルール

- 「実務経験」と「公開用デモ」のラベルを分けています。追加するときも、どちらかを必ず付けてください。
- 成果数値は、確認できる実績（Python による情報収集の自動化：月約1時間 → 約2分）だけを掲載しています。
- デモの処理件数（135行など）は架空データの処理結果で、実務の成果ではありません。
- 所属先が分かる情報、社内データ、社内の画面、非公開コードは掲載していません。

## GitHub Pages での公開手順

1. GitHub で新しいリポジトリを作成します。無料プランで GitHub Pages を使う場合、リポジトリは Public にする必要があります。リポジトリ名とアカウント名は公開URLに含まれるため、本名などを含めないか確認してください。
2. このフォルダの中身をリポジトリに登録します。

   ```bash
   cd portfolio
   git init
   git add .
   git commit -m "ポートフォリオサイトを追加"
   git branch -M main
   git remote add origin https://github.com/<アカウント名>/<リポジトリ名>.git
   git push -u origin main
   ```

   コミットには Git に設定した名前とメールアドレスが記録され、公開されます。事前に `git config user.name` と `git config user.email` で確認してください。

3. GitHub のリポジトリ画面で **Settings → Pages** を開きます。
4. **Build and deployment** の Source で **Deploy from a branch** を選び、Branch を **main**、フォルダを **/ (root)** にして **Save** を押します。
5. 数分後、同じ画面に公開URL（`https://<アカウント名>.github.io/<リポジトリ名>/`）が表示されます。

更新するときは、ファイルを編集してから次を実行します。

```bash
git add .
git commit -m "更新内容"
git push
```

## 実装していない機能

- **問い合わせフォーム**：サーバー側の処理が必要なため設置していません。問い合わせは出品ページへのリンクで受け付ける構成です。
- **アクセス解析、SNS共有用の画像（OGP）**：設定していません。必要になった時点で追加してください。

## デモについて

`demo/sales-cleanup/` に、架空の売上明細CSVを整形・集計する Python スクリプトがあります。
実行方法と処理内容は [demo/sales-cleanup/README.md](demo/sales-cleanup/README.md) を参照してください。
