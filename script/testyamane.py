import os
import datetime
# from IPython import embed
from google.cloud import storage
import pdb

# client = storage.Client(project_name)
# bucket = client.get_bucket(bucket_name)

# def write_log(file_name):
#   with open(file_name, 'w') as log_f:
#     log_f.write("お仕事No: 111112222211")
#     log_f.write("\r\n")
#     log_f.write("smartから求人を取得することができなかったため追加されませんでした。")
#     log_f.write("\r\n")
#     log_f.write("\r\n")

# def upload_to_gcs(file_name):
#   blob = storage.Blob(file_name, bucket)
#   blob.upload_from_filename(file_name)

BUCKET_NAME = 'trancom-data-convert'

def get_file_list_from_gcs():
  client = storage.Client()
  dirs = client.list_blobs(BUCKET_NAME)
  return dirs

def file_download_from_gcs(dir):
  file_name = dir.name.split('/')
  client = storage.Client()
  bucket = client.get_bucket(BUCKET_NAME)
  data = bucket.blob(dir.name)
  data.download_to_filename( './logs/' + file_name[1])

def main():
  # gcsにアクセス
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'spreadsheet_service_account.json'
  # project_name = 'single-mix-174909'
  # start_time = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
  # file_name = 'log/unsent_recruit_' + start_time + '.log'

  dirs = get_file_list_from_gcs()

  for dir in dirs:
    file_download_from_gcs(dir)

  #write_log(file_name)
  #upload_to_gcs(file_name)


if __name__ == "__main__":
  main()