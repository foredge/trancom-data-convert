# coding: utf-8
import asyncio
from datetime import datetime, date, timedelta
from email import encoders, utils
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import glob
import mimetypes
import smtplib
import sys
import os
import pdb
import re
import requests
import time

FROM_ADDRESS = os.environ['FROM_ADDRESS']
SUBJECT = '【要ご確認】ネクスト求人ドットコム連携エラー案件'
BODY = 'ご担当者様\n' \
       '\n' \
       'SMARTからネクスト求人ドットコムへの連携時に\n' \
       'エラーとなった案件がありましたのでご連絡いたします。\n' \
       '\n' \
       '詳細は添付ファイルよりご確認ください。\n' \
       '\n' \
       'ご不明点がございましたら、以下の連絡先までお願いします。\n' \
       '\n' \
       'baitai@foredge.co.jp'

def send_mail(to_address, file_path):
    return requests.post(
        "https://api.mailgun.net/v3/" + os.environ['MAIL_DOMAIN'] + "/messages",
        auth=("api", os.environ['MAILGUN_API_KEY']),
        files=[("attachment", open(file_path))],
        data={"from": FROM_ADDRESS,
              "to": to_address,
              "subject": SUBJECT,
              "text": BODY})

def make_send_file(file_path):
    send_body = ''
    # logs配下のファイルを 読込 -> 削除 -> まとめる
    for path in glob.glob("./logs/*"):
        with open(path) as rows:    # 読み込み
            send_body += rows.read()
            os.remove(path) # ファイル削除
    with open(file_path , mode='w') as f:   # 書き込み
        f.write(send_body)

def main():
    try:
        to_addresses = [
            'gadmin@foredge.co.jp'
        ]
        # addresses = [
        #     'ta_mori@trancom.co.jp',
        #     'f_tanaka@trancom.co.jp',
        #     'hiro_watanabe@trancom.co.jp',
        #     'baitai@foredge.co.jp'
        # ]
        file_path = './send_mails/' + format(datetime.today(), '%Y-%m-%d') + '.txt'

        make_send_file(file_path)

        for to_address in to_addresses:
            send_mail(to_address, file_path)
        return 'OK'
    except:
        return 'FAILD'

if __name__ == "__main__":
    main()