# trancom-data-convert

- [開発に必要なもの](#開発に必要なもの)
- [初回セットアップ](#初回セットアップ)

# 開発に必要なもの

- Docker
- PyCharm(VSCodeでもok)

---

# 初回セットアップ

- .envを追加
中身は管理者に聞いてください

## 開発用()
```shell
$ make build
$ make up
$ make psh
---
$ python3 app.py
```

## 本番検証用
```shell
$ make prdbuild && make prdrun
```

## 処理実行URL
http://localhost:8000/

http://localhost:8000/mail


# SMARTシステムのACL対策について
SMARTにアクセスできるのは、
- 大阪オフィス
- 東京オフィス
- admin.foredge.club

からに限定されています。  
GoogleCloudRunではIPアドレスを限定することが難しいので、adminにsquidを立ててプロキシ経由でSMARTにアクセスするようにしています。

IPアドレスを追加するには、重さん経由でお客さんに依頼をしなくてはいけません。  
CloudRunのIPレンジを追加できるか聞いてみたけど、広すぎると言って断られたらしい。

※2020/6/29のシステム更新によって、既存のnginxプロキシでは動かなくなりました。  
　nginxでは特別なパッチを当てないと、CONNECTメソッドが使えないのですが、今まではなんで動いていたのかわからない。  
　推測するに、`-k http://xxxx` のように書かれていたので、それまではhttpでSMARTにアクセスしていて、更新によってhttpでアクセス出来なくなったか？
