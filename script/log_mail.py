# coding: utf-8
import smtplib
import sys
from email import encoders, utils
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mimetypes
import glob
import re
import datetime
from flask import Flask
import requests

app = Flask(__name__)

JOB_CONVERT_RULE = {}
# TO_ADDRESS = 'aidan@foredge.co.jp'
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

# def attachment(filename):
#     fd = open(filename, 'rb')
#     mimetype, mimeencoding = mimetypes.guess_type(filename)
#     if mimeencoding or (mimetype is None):
#         mimetype = 'application/octet-stream'
#     maintype, subtype = mimetype.split('/')
#     if maintype == 'text':
#         retval = MIMEText(fd.read(), _subtype=subtype, _charset="shift_jisx0213")
#     else:
#         retval = MIMEBase(maintype, subtype)
#         retval.set_payload(fd.read())
#         encoders.encode_base64(retval)
#     retval.add_header('Content-Disposition', 'attachment', filename=filename.lstrip('./log/'))
#     fd.close()
#     return retval


# def create_message(fromaddr, toaddr, subject, message, filename):
#     msg = MIMEMultipart()
#     msg['To'] = toaddr
#     msg['From'] = 'sys@foredge.co.jp'
#     msg['Subject'] = subject
#     msg['Date'] = utils.formatdate(localtime=True)
#     msg['Message-ID'] = utils.make_msgid()

#     body = MIMEText(message, _subtype='plain')
#     msg.attach(body)

#     msg.attach(attachment(filename))
#     return msg.as_string()


def send_mail(from_addr, to_addrs, subject, body, filename):
    return requests.post(
        "https://api.mailgun.net/v3/" + os.environ['MAIL_DOMAIN'] + "/messages",
        auth=("api", os.environ['MAILGUN_API_KEY']),
        files=[("attachment", open(filename))],
        data={"from": from_addr,
              "to": to_addrs,
              "cc": cc_addrs,
              "subject": subject,
              "text": body})

# def send(from_addr, to_addrs, msg):
#     smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
#     smtpobj.ehlo()
#     smtpobj.starttls()
#     smtpobj.ehlo()
#     smtpobj.login(os.environ['FROM_ADDRESS'], os.environ['MY_PASSWORD'])
#     smtpobj.sendmail(from_addr, to_addrs, msg)
#     smtpobj.close()


@app.route('/log_mail')
def main():
    addresses = [
        'iwakuni@foredge.co.jp'
    ]
    # addresses = [
    #     'ta_mori@trancom.co.jp',
    #     'f_tanaka@trancom.co.jp',
    #     'hiro_watanabe@trancom.co.jp',
    #     'baitai@foredge.co.jp'
    # ]
    for address_i, address in enumerate(addresses):
        fromaddr = os.environ['FROM_ADDRESS']
        toaddr = address

        file_list = glob.glob("./log/unsent_recruit_201*")

        file = ''
        number = 0
        for i, row in enumerate(file_list):
            if int(re.match(".*?(\d+)", row).group(1)) > number:
                number = int(re.match(".*?(\d+)", row).group(1))
                file = row
        if file != '' and int(re.match(".*?(\d+)", file).group(1)) > int(datetime.datetime.today().strftime("%Y%m%d") + '000000'):
            send_mail(fromaddr, toaddr, SUBJECT, BODY, file)
            # message = create_message(fromaddr, toaddr, SUBJECT, BODY, file)
            # send(fromaddr, toaddr, message)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(8000))