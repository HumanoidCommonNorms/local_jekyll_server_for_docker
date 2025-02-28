# local_jekyll_server_for_docker

Dockerを使用して、ローカルでGitHub pageの表示を確認するためのテスト環境です。
設定を行うと[http://localhost:8888](http://localhost:8888)でアクセスできるようになります。

## ローカルサーバーのセットアップ

* ビルドしたいフォルダを指定してください。
* ファイルを更新後に、再実行すればページを作り直します。

```bash
local_jekyll.py ${ビルドしたいフォルダを指定してください}
```

その他のオプションは以下のコマンドで確認できます。

```bash
local_jekyll.py --help
```
