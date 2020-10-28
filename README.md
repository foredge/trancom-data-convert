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
クローリングとCSVデータを基にしたデータの同期  
http://localhost:8000/

エラーメールの送信  
http://localhost:8000/mail

## 資料
変換ルールについてのスプレッドシート  
https://docs.google.com/spreadsheets/d/1ZeTgqvqx28YFOvr4118cJKYj3ZxqPkojGl8fYkNI17Q/edit

トランコム関連の資料  
https://drive.google.com/drive/u/0/folders/0B0BPCxlRywtCbHkyajNlT0VRWms

過去のCSVログ  
https://drive.google.com/drive/u/0/folders/1f87O-xRBLynhzhoV-bLGwaKCfZR5L9JA

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


## 大阪オフィス以外のネットワークからSMARTにアクセスする
adminサーバでproxyを運用してますが、そこにもACLをかけてます。  
外部ネットワークからこれを利用するには大阪オフィスのVPN経由でプログラムを実行して下さい。

### VPN接続されている前提で
ubuntuでstatic routeを追加する方法
```
$ sudo route add -host 35.194.117.51 dev tun0
```

macではdevオプションは指定できないので、以下のようにvpnのgatewayを指定する必要があります。
```
$ sudo route add -net 35.194.117.51 10.20.0.9
```
`10.20.0.9` がvpn gateway
