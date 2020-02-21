# 参考にしたサイト
# https://hodalog.com/use-selenium-on-docker/
FROM python:3.7-alpine

ENV APP_HOME /app
ENV FLASK_ENV development
ENV PYTHONIOENCODING utf-8
WORKDIR $APP_HOME
COPY . .

RUN apk add --update \
      curl \
      wget \
      vim \
    # Add chromium and dependences
      udev \
      ttf-freefont \
      chromium \
      chromium-chromedriver \
    # Add Japanese font
    && mkdir noto \
    && wget -P /app/noto https://noto-website.storage.googleapis.com/pkgs/NotoSansCJKjp-hinted.zip \
    && unzip /app/noto/NotoSansCJKjp-hinted.zip -d /app/noto \
    && mkdir -p /usr/share/fonts/noto \
    && cp /app/noto/*.otf /usr/share/fonts/noto \
    && chmod 644 -R /usr/share/fonts/noto/ \
    && fc-cache -fv \
    && rm -rf /app/noto \
    # Add selenium
    && pip install \
      selenium \
      PyDrive \
      google-api-python-client \
      google-auth \
      google-auth-httplib2 \
      google-cloud-storage \
      httplib2 \
      nose \
      oauth2client \
      gspread \
      Flask

CMD flask run --host='0.0.0.0' --port=8000