build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

sh:
	docker-compose exec python3 bash
	# docker-compose exec chrome bash

# ログ確認
logf:
	docker-compose logs -f python3

# selenium vnc
# pass: secret
vnc:
	open vnc://localhost:15900


pushgcr:
	gcloud config set project single-mix-174909
	docker build -t asia.gcr.io/single-mix-174909/trancom -f ./script/Dockerfile ./
	docker push asia.gcr.io/single-mix-174909/trancom


deployCloudRun:
	gcloud beta run deploy --image asia.gcr.io/single-mix-174909/trancom