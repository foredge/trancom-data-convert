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

開発用
```shell
$ make build && make up
```

本番検証用
```shell
$ make prdbuild && make prdrun
```
http://localhost:8000/
