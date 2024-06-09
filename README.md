# local_jekyll_server_for_docker

Dockerを使用して、ローカルでGitHub pageの表示を確認するためのテスト環境です。
設定を行うと[http://localhost:8000](http://localhost:8000)でアクセスできるようになります。

## ローカルサーバーのセットアップ

```bash
# 下記コマンドを実行してください。
# 第一引数にはビルドしたいフォルダを指定してください。
# ファイルを更新し再実行すれば、Dockerコンテナを再起動をしてjekyllのビルドを行います。
server.py {ビルドしたいフォルダを指定してください}

# Dockerイメージを作り直したい場合は、--setupをつけてください。
server.py  {ビルドしたいフォルダを指定してください} --setup
# Dockerコンテナを作り直したい場合は、--remake_container_onlyをつけてください。
server.py  {ビルドしたいフォルダを指定してください} --remake_container_only
```

その他のオプションは以下のコマンドで確認できます。

```bash
server.py --help
```
