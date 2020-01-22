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


JOB_CONVERT_RULE = {}
FROM_ADDRESS = 'hideyasu.yamaguchi@foredge.co.jp'
MY_PASSWORD = 'reiri1113'
# TO_ADDRESS = 'hideyasu.yamaguchi@foredge.co.jp'
# TO_ADDRESS = 'baitai@foredge.co.jp'
TO_ADDRESS = 'aidan@foredge.co.jp'
BCC = ''
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

def attachment(filename):
    fd = open(filename, 'rb')
    mimetype, mimeencoding = mimetypes.guess_type(filename)
    if mimeencoding or (mimetype is None):
        mimetype = 'application/octet-stream'
    maintype, subtype = mimetype.split('/')
    if maintype == 'text':
        retval = MIMEText(fd.read(), _subtype=subtype, _charset="shift_jisx0213")
    else:
        retval = MIMEBase(maintype, subtype)
        retval.set_payload(fd.read())
        encoders.encode_base64(retval)
    retval.add_header('Content-Disposition', 'attachment', filename=filename.lstrip('./log/'))
    fd.close()
    return retval


def create_message(fromaddr, toaddr, subject, message, filename):
    msg = MIMEMultipart()
    msg['To'] = toaddr
    msg['From'] = 'sys@foredge.co.jp'
    msg['Subject'] = subject
    msg['Date'] = utils.formatdate(localtime=True)
    msg['Message-ID'] = utils.make_msgid()

    body = MIMEText(message, _subtype='plain')
    msg.attach(body)

    msg.attach(attachment(filename))
    return msg.as_string()


def send(from_addr, to_addrs, msg):
    smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(FROM_ADDRESS, MY_PASSWORD)
    smtpobj.sendmail(from_addr, to_addrs, msg)
    smtpobj.close()


if __name__ == '__main__':

    addresses = [
        'ta_mori@trancom.co.jp',
        'f_tanaka@trancom.co.jp',
        'hiro_watanabe@trancom.co.jp',
        'baitai@foredge.co.jp'
    ]
    for address_i, address in enumerate(addresses):
        fromaddr = FROM_ADDRESS
        toaddr = address

        file_list = glob.glob("./log/unsent_recruit_201*")

        file = ''
        number = 0
        for i, row in enumerate(file_list):
            if int(re.match(".*?(\d+)", row).group(1)) > number:
                number = int(re.match(".*?(\d+)", row).group(1))
                file = row
        if file != '' and int(re.match(".*?(\d+)", file).group(1)) > int(datetime.datetime.today().strftime("%Y%m%d") + '000000'):
            message = create_message(fromaddr, toaddr, SUBJECT, BODY, file)
            send(fromaddr, toaddr, message)
