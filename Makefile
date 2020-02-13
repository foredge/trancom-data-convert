build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

psh:
	docker-compose exec python3 ash
nsh:
	docker-compose exec nginx bash

# ログ確認
logf:
	docker-compose logs -f python3

# selenium vnc
# pass: secret
vnc:
	open vnc://localhost:5900


# 本番検証用
prdbuild:
	docker build -t trancom ./script/

prdrun:
	docker run -v $(pwd)/script:/app --env-file .env -p 8000:8000 trancom


# GoogleCloudRegistryにpush
pushgcr:
	gcloud config set project single-mix-174909
	docker build -t asia.gcr.io/single-mix-174909/trancom -f ./script/Dockerfile ./script
	docker push asia.gcr.io/single-mix-174909/trancom

# CloudRunにdeploy
deployCloudRun:
	gcloud beta run deploy --image asia.gcr.io/single-mix-174909/trancom