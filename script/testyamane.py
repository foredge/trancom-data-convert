import os
import datetime
from IPython import embed
from google.cloud import storage

client = storage.Client(project_name)
bucket = client.get_bucket(bucket_name)

def write_log(file_name):
  with open(file_name, 'w') as log_f:
    log_f.write("お仕事No: 111112222211")
    log_f.write("\r\n")
    log_f.write("smartから求人を取得することができなかったため追加されませんでした。")
    log_f.write("\r\n")
    log_f.write("\r\n")

def upload_to_gcs(file_name):
  blob = storage.Blob(file_name, bucket)
  blob.upload_from_filename(file_name)

def get_file_list_from_gcs(bucket_name):
  bucket = client.get_bucket(bucket_name)
  dirs = bucket.list_blobs(prefix="a/", delimiter="/")
  [print(x) for x in dirs]

def main():
  # gcsにアクセス
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'spreadsheet_service_account.json'
  bucket_name = 'trancom-data-convert'
  project_name = 'single-mix-174909'

  start_time = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
  file_name = 'log/unsent_recruit_' + start_time + '.log'

  #write_log(file_name)
  #upload_to_gcs(file_name)
  get_file_list_from_gcs(bucket_name)
