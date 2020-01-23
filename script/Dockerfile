FROM python:3.7


FROM python:3

ENV APP_HOME /app
ENV FLASK_ENV development
WORKDIR $APP_HOME
COPY . .

RUN set -x && \
  apt-get update && apt-get install -y vim && \
  pip install \
  selenium \
  PyDrive \
  google-api-python-client \
  google-auth \
  google-auth-httplib2 \
  httplib2 \
  nose \
  oauth2client \
  gspread \
  Flask

CMD flask run --host='0.0.0.0' --port=8000