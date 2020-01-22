FROM python:3

ENV APP_HOME /app
WORKDIR $APP_HOME

RUN set -x && \
  apt-get update && \
  apt-get install -y vim && \
  pip install selenium && \
  pip install PyDrive && \ 
  pip install google-api-python-client && \
  pip install google-auth && \
  pip install google-auth-httplib2 && \
  pip install httplib2 && \
  pip install nose && \
  pip install oauth2client && \
  pip install gspread && \
  pip install Flask gunicorn

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app