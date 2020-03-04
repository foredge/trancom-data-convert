# coding: UTF-8
import datetime
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from time import sleep
import os
import subprocess
import json
import csv
import urllib.parse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import shutil
import pdb
import requests
from google.cloud import storage

JOB_CONVERT_RULE = {}
SUBJECT = 'トランコム自動アップロードが失敗しました。'
BODY = ''
BUCKET_NAME = 'trancom-data-convert'

# ./log/ 配下にtest.logを作成するとGCSに上がる

# GCSにファイルアップロードして削除
def upload_file_to_gcs(start_time):
    local_file_name = "unsent_recruit_" + start_time + ".log"
    local_file_name = "test.log"
    local_file_path = "./log/" + local_file_name
    destination_blob_name = 'log/' + local_file_name
    if os.path.exists(local_file_path):
        bucket = storage.Client().get_bucket(BUCKET_NAME)
        data = bucket.blob(destination_blob_name)
        data.upload_from_filename(local_file_path)
        print('File {} uploaded to {}.'.format(
            local_file_name,
            destination_blob_name))
        os.remove(local_file_path)
        print('{} File deleted .'.format(local_file_name))

def main():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'spreadsheet_service_account.json'
    # 日本時間に合わせる
    start_time = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y%m%d%H%M%S")
    try:
        global JOB_CONVERT_RULE
        JOB_CONVERT_RULE = get_job_convert_rule()
        start_time = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
        upload_file_to_gcs(start_time)
        return f'ok!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    except:
        send_slack(subject + "\n" + traceback.format_exc())
        return f'Except!!'

if __name__ == "__main__":
    main()
