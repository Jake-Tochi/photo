
# 全国物流ネットワーク協会 フォトギャラリー

2025年 全国物流ネットワーク協会 板橋グループ様 研修会で撮影した写真を公開するための静的サイトです。フレームワークや外部 CDN に依存せず、純粋な HTML / CSS / JavaScript で構成しています。`tools/build_gallery.py` を実行することで写真メタデータ (`photos/gallery.json`) を自動生成できます。

## ディレクトリ構成

```
/
├─ index.html         # トップページ本体
├─ styles.css         # レイアウト・スタイル定義
├─ app.js             # ギャラリー描画とライトボックス制御
├─ assets/
│   └─ rogo.webp      # 協会ロゴ（クリックで公式サイトへ遷移）
├─ photos/
│   ├─ *.jpg          # 公開用のオリジナル写真
│   └─ gallery.json   # 自動生成されるメタデータ
└─ tools/
    └─ build_gallery.py  # メタデータ生成＆サムネイル作成スクリプト
```

## 使い方

1. `E:\zenryukyo` 直下に追加したい写真（jpg/jpeg/png/webp）を配置します。
2. ロゴ画像を差し替える場合は `--logo` オプションでパスを指定します（既定: `E:\Download\rogo.webp`）。
3. 以下のコマンドを実行してギャラリーを更新します。

```powershell
python tools/build_gallery.py
```

スクリプト実行後、`index.html` のギャラリー領域と `#gallery-data` 内の JSON が最新の写真リストに差し替わります。

### オプション

- `--source <PATH>`: 写真を探索する元ディレクトリ（既定: リポジトリルート）
- `--logo <PATH>`: `assets/rogo.webp` へコピーするロゴのパス
- `--thumb-size <INT>`: 生成するサムネイルの最大辺（デフォルト 1200px）
- `--skip-copy`: 元フォルダから `photos/` へのコピーを省略
- `--skip-thumbs`: Pillow がインストール済みでもサムネイル生成を行わない

> **サムネイル生成について**
> Pillow (`pip install pillow`) が利用可能な場合、自動的に `photos/thumbs/` を生成し、`gallery.json` に `thumb` 情報を追加します。Pillow がない場合はオリジナル画像の寸法を解析し、サムネイル生成はスキップします。

## ローカル確認

簡易的には以下のようにローカルサーバーを立ち上げてブラウザで表示できます。

```powershell
python -m http.server 8000
```

`http://localhost:8000/` をブラウザで開くとギャラリーを確認できます。

## デプロイ

生成されたファイル一式を GitHub へコミットし、`main` ブランチから GitHub Pages（`/` ルート公開）を有効化すると、そのまま公開できます。写真を追加する際は同じ手順でスクリプトを再実行し、更新された `photos/` ディレクトリと `gallery.json` をコミットしてください。

## ライセンス

写真素材およびロゴは提供元の許諾範囲でのみ利用してください。その他のコードは MIT ライセンス相当での再利用を歓迎します。
