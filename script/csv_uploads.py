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
import traceback

JOB_CONVERT_RULE = {}
SUBJECT = 'トランコム自動アップロードが失敗しました。'
BODY = ''
BUCKET_NAME = 'trancom-data-convert'

def send_mail(from_addr, to_addrs, subject, body):
    return requests.post(
        "https://api.mailgun.net/v3/" + os.environ['MAIL_DOMAIN'] + "/messages",
        auth=("api", os.environ['MAILGUN_API_KEY']),
        data={"from": from_addr,
              "to": to_addrs,
              "bcc": os.environ['TO_BCC_ADDRESS'],
              "subject": subject,
              "text": body})

def send_error_mail(text):
    send_mail(os.environ['FROM_ADDRESS'], os.environ['TO_ADDRESS'], SUBJECT, text)

def send_slack(text):
    requests.post(os.environ['SLACK_WEBHOOK_URL'], data=json.dumps({
        'text': text,
        'username': u'trancom',
        'icon_emoji': u':ghost:',
        'link_names': 1,
    }))

def checker(start_time):
    with open('csv/trancom/trancom_origin_' + start_time + '.csv', 'r',
              encoding='shift_jisx0213') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if row.__len__() == 138:
                print(row.__len__())

def next_login(driver):
    driver.get("https://trancom:sc@manage.4104510.com/manager/login")
    driver.find_element_by_id('ManagerUsername').send_keys(os.environ['NEXT_MANAGER_USER_NAME'])
    driver.find_element_by_id('ManagerPassword').send_keys(os.environ['NEXT_MANAGER_PASSWORD'])
    driver.find_element_by_id("loginButton").click()

def csv_upload_to_410510(start_time):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--window-size=1366,768')

    driver = webdriver.Chrome(options=options)
    # リモートブラウザに接続(開発用)
    # driver = webdriver.Remote(command_executor='http://selenium-hub:4444/wd/hub',desired_capabilities=DesiredCapabilities.CHROME)
    next_login(driver)

    driver.get("https://trancom:sc@manage.4104510.com/job/csv_import/")
    driver.find_element_by_id("JobDetailCsvFile").send_keys(os.getcwd() + '/csv/trancom/trancom_origin_' + start_time + '.csv')
    driver.find_element_by_class_name('button01').click()
    if driver.find_elements_by_class_name('error-message'):
        send_error_mail(driver.find_elements_by_class_name('error-message')[0].text)
        driver.close()
        return 0
    driver.find_element_by_class_name('button01').click()
    driver.close()

def csv_download_from_next(start_time):
    print('nextのcsvをダウンロード')
    new_dir_path = 'csv/next/' + start_time
    os.mkdir(new_dir_path)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--window-size=1366,768')
    driver = webdriver.Chrome(options=options)
    # リモートブラウザに接続(開発用)
    # driver = webdriver.Remote(command_executor='http://selenium-hub:4444/wd/hub',desired_capabilities=DesiredCapabilities.CHROME)

    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    driver.execute("send_command", {
        'cmd': 'Page.setDownloadBehavior',
        'params': {
            'behavior': 'allow',
            'downloadPath': new_dir_path
        }
    })

    next_login(driver)

    driver.find_element_by_class_name('inputSubmit').click()
    sleep(10)
    driver.close()
    driver.quit()

def download_curl_to_smart(start_time):
    print("Login to SMART management site.")
    login_curl_command = ("curl -c ./cookie.txt -x " + os.environ['PROXY_SERVER'] + " 'https://talent.metastasys.biz/sinfoniacloud/api/Login.json'"
                          " -H 'Connection: keep-alive'"
                          " -H 'Accept: application/json, text/javascript, */*; q=0.01'"
                          " -H 'X-Requested-With: XMLHttpRequest'"
                          " -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'"
                          " -H 'Content-Type: application/json'"
                          " -H 'Origin: https://talent.metastasys.biz'"
                          " -H 'Sec-Fetch-Site: same-origin'"
                          " -H 'Sec-Fetch-Mode: cors'"
                          " -H 'Sec-Fetch-Dest: empty'"
                          " -H 'Referer: https://talent.metastasys.biz/appl/menu.html'"
                          " -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8'"
                          " --data-binary $'{\"body\":{\"companyCD\":\"SMART\",\"userID\":\"" + os.environ['SMART_USER'] + "\",\"password\":\"" + os.environ['SMART_PASS'] + "\"}}\r\n'"
                          " --compressed -s")
    os.system(login_curl_command)

    print("Get the list of recruit data.")
    # 検索オプション
    #   掲載区分：掲載中 -> POST_TYPE=0
    list_curl_command = ("curl -b ./cookie.txt -x " + os.environ['PROXY_SERVER'] + " 'https://talent.metastasys.biz/sinfoniacloud/api/SearchApprovedAnken.json"
                         "?_qt=false&_ns=SMART.facade.anken&_limitCount=2000&JOB_NO=&ANKEN_NAME_LIKE=&COMPANY_NO=&PREFECTURE_LIKE=&CITY_LIKE=&OFFICE_NO=&OFFICE_STAFF_NO=&OCCUPATION_CATEGORY=&AGE_MAX=&GENDER=&PREDETERMINED_ALLOWANCE_HOUR=&PREDETERMINED_ALLOWANCE_MONTH=&HOLIDAY_DESCRIPTION_LIKE=&DAY_SHIFT_ONLY=0&NIGHT_SHIFT_ONLY=0&TWO_SHIFT=0&THREE_SHIFT=0&OTHER=0&QUALIFICATION=&MEDIA_AGENCY_NO=&MEDIA_AGENCY_NAME=&EMPLOYMENT_TYPE=&ANKEN_RANK=&HIRING_RANK=&POST_TYPE=0&DORMITORY=0&DORMITORY_FEE_SUBSIDY=&FOREIGN_NATIONALITY_OK=0&TATTOO_OK=0'"
                         " -H 'Connection: keep-alive'"
                         " -H 'Accept: application/json, text/javascript, */*; q=0.01'"
                         " -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'"
                         " -H 'X-Requested-With: XMLHttpRequest'"
                         " -H 'Sec-Fetch-Site: same-origin'"
                         " -H 'Sec-Fetch-Mode: cors'"
                         " -H 'Sec-Fetch-Dest: empty'"
                         " -H 'Referer: https://talent.metastasys.biz/appl/html/anken/AnkenList.html'"
                         " -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8'"
                         " --compressed -s")
    list_curl_data = subprocess.Popen([list_curl_command], stdout=subprocess.PIPE, shell=True).stdout.read()
    return list_curl_data

def csv_download_from_smart(start_time):
    print('smartのcsvをダウンロード')
    with open('csv/smart/smart_origin_' + start_time + '.csv', 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow('お仕事No,職種,職種詳細1,職種詳細2,雇用形態,営業所,担当者,都道府県,市区町村,住所詳細,最寄駅,お仕事内容,シフト１・開始時刻,シフト１・終了時刻,シフト２・開始時刻,シフト２・終了時刻,シフト３・開始時刻,シフト３・終了時刻,休日,勤務シフト,休日･シフト備考,月収例,応募条件,必要資格,給与見込額,入社祝金,ミニボーナス,満了祝金,赴任旅費,引越費用,その他手当,給与単位,所定(円),シフト１・所定(日),シフト１・残業(H),シフト１・開始時刻,シフト１・終了時刻,シフト１・実働(H),シフト１・休憩時間(M),シフト２・所定(日),シフト２・残業(H),シフト２・開始時刻,シフト２・終了時刻,シフト２・実働(H),シフト２・休憩時間(M),シフト３・所定(日),シフト３・残業(H),シフト３・開始時刻,シフト３・終了時刻,シフト３・実働(H),シフト３・休憩時間(M),見出し,入社まで期間,高時給,高月給,交通費支給,扶養範囲OK,マイカー通勤,駐車場,送迎,日勤固定,夜勤固定,2交替,3交替,残業休出,寮･社宅,寮費,入寮期間,間取り,通勤距離,水道光熱,家電設備,築年数,駐車場,最寄駅,商業施設,未経験OK,男性活躍中,女性活躍中,シニア活躍中,ペア･家族OK,資格スキルサポート,オープニング,大量募集,受動喫煙防止(対策有無),受動喫煙防止(対策方法),受動喫煙防止(特記事項)'.split(','))

    records = json.loads(download_curl_to_smart(start_time))

    for i, record in enumerate(records['body']['_obj0']):
        # 各求人をCSVファイルとしてダウンロード
        # 一覧で取得したデータをサーバに渡してあげないといけないのでURLエンコードしてリクエストに付加する
        req_record = urllib.parse.quote(str(record))
        recruit_curl_command = ("curl -b ./cookie.txt -x " + os.environ['PROXY_SERVER'] + " 'https://talent.metastasys.biz/sinfoniacloud/api/OutputAnkenInformation.json'"
                                " -H 'Connection: keep-alive'"
                                " -H 'Cache-Control: max-age=0'"
                                " -H 'Upgrade-Insecure-Requests: 1'"
                                " -H 'Origin: https://talent.metastasys.biz'"
                                " -H 'Content-Type: application/x-www-form-urlencoded'"
                                " -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'"
                                " -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'"
                                " -H 'Sec-Fetch-Site: same-origin'"
                                " -H 'Sec-Fetch-Mode: navigate'"
                                " -H 'Sec-Fetch-User: ?1'"
                                " -H 'Sec-Fetch-Dest: document'"
                                " -H 'Referer: https://talent.metastasys.biz/appl/html/anken/AnkenList.html'"
                                " -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8'"
                                " --data-raw '"
                                "_responseType=RedirectIfError"
                                "&_ns=SMART.facade.anken"
                                "&_qt=false"
                                "&_body=%7B%22"
                                "_obj0%22%3A%5B" + req_record +
                                "%5D%7D'"
                                " --compressed -s")
        print(str(i) + ". Downloading recruit detail JOB_NO: " + record['JOB_NO'])
        next_records = subprocess.Popen([recruit_curl_command],stdout=subprocess.PIPE, shell=True).stdout.read().decode('utf-8').split('\n', 1)

        # リクエストをした後にエラーが帰ってきた場合
        # 4/18, 19に2699-0006が上がってこなかった件の調査
        # しかし4/22の時点で該当案件が引っかからなくなってしまった
        formatted_start_time = datetime.datetime.strptime(start_time, "%Y%m%d%H%M%S").strftime("%Y年%m月%d日%H時%M分")
        if 'errorInfo' in next_records[0]:
            with open('log/unsent_recruit_' + start_time + '.log', 'a') as log_f:
                log_f.write("お仕事No: " + urllib.parse.quote(record['jobNo']))
                log_f.write("\r\n")
                log_f.write("smartから求人を取得することができなかったため追加されませんでした。 " + formatted_start_time)
                log_f.write("\r\n")
                log_f.write("\r\n")

        with open('csv/smart/smart_origin_' + start_time + '.csv', 'a') as f:
            insert_record = []
            for index, next_record in enumerate(next_records):
                if index == 0 or next_record == '':
                    continue
                insert_record += next_record.split('","')
                insert_record[0] = insert_record[0][1:]
                insert_record[-1] = insert_record[-1].replace('"', '')
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(insert_record)

def exist_records_from_next(start_time):
    exist_records = []

    with open('csv/next/' + start_time + '/job_' + start_time[:8] + '.csv', 'r',
              encoding='shift_jisx0213') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if (i == 0):
                continue
            exist_records.append(row)
    return exist_records

def csv_make_for_trancom(start_time):
    print('trancomのcsvを作成')
    # ---デバッグ用のコード---
    # start_time = glob.glob('csv/next/*')[0].split('/')[2]
    # start_time = '20190617110509'
    # ----------------------

    exist_records = exist_records_from_next(start_time)

    with open('csv/trancom/trancom_origin_' + start_time + '.csv', 'w', encoding='shift_jisx0213') as trancom_f:
        head = "求人情報ID,公開開始日時,公開終了日時,掲載優先順位,求人登録企業ID,求人登録企業名,分類,タイトル,キャッチコピー,画像,求人掲載企業名,企業ロゴ,業種,職種,雇用形態 派遣 表示,雇用形態 派遣 給与単位,雇用形態 派遣 給与（低）,雇用形態 派遣 給与（高）,雇用形態 派遣 備考,雇用形態 請負 表示,雇用形態 請負 給与単位,雇用形態 請負 給与（低）,雇用形態 請負 給与（高）,雇用形態 請負 備考,雇用形態 職業紹介 表示,雇用形態 職業紹介 給与単位,雇用形態 職業紹介 給与（低）,雇用形態 職業紹介 給与（高）,雇用形態 職業紹介 備考,雇用形態 紹介予定派遣 表示,雇用形態 紹介予定派遣 給与単位,雇用形態 紹介予定派遣 給与（低）,雇用形態 紹介予定派遣 給与（高）,雇用形態 紹介予定派遣 備考,雇用形態 契約社員・パート・アルバイト 表示,雇用形態 契約社員・パート・アルバイト 給与単位,雇用形態 契約社員・パート・アルバイト 給与（低）,雇用形態 契約社員・パート・アルバイト 給与（高）,雇用形態 契約社員・パート・アルバイト 備考,雇用形態 正社員 表示,雇用形態 正社員 給与単位,雇用形態 正社員 給与（低）,雇用形態 正社員 給与（高）,雇用形態 正社員 備考,勤務地（都道府県）,勤務地（市区町村）,勤務地（住所）,最寄駅1（路線）,最寄駅1（駅名）,最寄駅1（移動方法）,最寄駅1（移動時間）,最寄駅2（路線）,最寄駅2（駅名）,最寄駅2（移動方法）,最寄駅2（移動時間）,最寄駅3（路線）,最寄駅3（駅名）,最寄駅3（移動方法）,最寄駅3（移動時間）,残業,勤務期間,休日・休暇,勤務時間1（開始時間）,勤務時間1（終了時間）,勤務時間1（備考）,勤務時間2（開始時間）,勤務時間2（終了時間）,勤務時間2（備考）,勤務時間3（開始時間）,勤務時間3（終了時間）,勤務時間3（備考）,勤務時間4（開始時間）,勤務時間4（終了時間）,勤務時間4（備考）,勤務時間5（開始時間）,勤務時間5（終了時間）,勤務時間5（備考）,勤務時間6（開始時間）,勤務時間6（終了時間）,勤務時間6（備考）,勤務時間7（開始時間）,勤務時間7（終了時間）,勤務時間7（備考）,勤務時間8（開始時間）,勤務時間8（終了時間）,勤務時間8（備考）,仕事内容,ここがポイント,応募資格,性別,対象年齢（低）,対象年齢（高）,フリー項目1（タイトル）,フリー項目1,フリー項目2（タイトル）,フリー項目2,フリー項目3（タイトル）,フリー項目3,HTML上部,HTML下部,職種（テキスト）,問い合わせ先：メールアドレス,問い合わせ先：電話番号,問い合わせ先：電話受付時間,お仕事No.,問い合わせ先：担当者,応募通知先,応募通知先（bcc）,メモ欄,作成日時,更新日時,削除フラグ,こだわり条件‐入社祝金,こだわり条件‐ミニボーナス,こだわり条件‐満了祝金,こだわり条件‐赴任旅費,こだわり条件‐引越費用,こだわり条件‐その他手当,こだわり条件‐高月給,こだわり条件‐交通費支給,こだわり条件‐扶養範囲OK,こだわり条件‐マイカー通勤,こだわり条件‐駐車場,こだわり条件‐送迎,こだわり条件‐日勤固定,こだわり条件‐夜勤固定,こだわり条件‐2交替,こだわり条件‐3交替,こだわり条件‐残業休出,こだわり条件‐寮･社宅,こだわり条件‐寮費無料,こだわり条件‐未経験OK,こだわり条件‐男性活躍中,こだわり条件‐女性活躍中,こだわり条件‐シニア活躍中,こだわり条件‐ペア･家族OK,こだわり条件‐資格スキルサポート,こだわり条件‐オープニング,こだわり条件‐大量募集"
        writer = csv.writer(trancom_f, lineterminator='\n')
        writer.writerow(head.split(','))

        # smartからnextに上げるためのcsvの変換作成
        with open('csv/smart/smart_origin_' + start_time + '.csv', 'r') as smart_f:
            reader = csv.reader(smart_f)
            with open('log/insert_' + start_time + '.log', 'a') as log_f:
                log_f.write("smartからnextの変換処理\n")
            for i, row in enumerate(reader):
                if i == 0 or row.__len__() == 0:
                    continue
                try:
                    insert_log(start_time, row)
                    record = csv_converter(row, exist_records)
                    # 見出し、職種、雇用時間が空の場合レコードを追加しない
                    if record[7] == '' or record[13] == '' or record[62] == '':
                        formatted_start_time = datetime.datetime.strptime(start_time, "%Y%m%d%H%M%S").strftime("%Y年%m月%d日%H時%M分")
                        with open('log/unsent_recruit_' + start_time + '.log', 'a') as log_f:
                            log_f.write("お仕事No: " + row[0])
                            log_f.write("\r\n")
                            if record[7] == '':
                                log_f.write("見出しが空のためレコードは追加されませんでした。 " + formatted_start_time)
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                            if record[13] == '':
                                log_f.write("職種詳細1: " + row[2])
                                log_f.write("\r\n")
                                log_f.write("職種詳細2: " + row[3])
                                log_f.write("\r\n")
                                log_f.write("職種変換表にないためレコードは追加されませんでした。 " + formatted_start_time)
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                            if record[62] == '':
                                log_f.write("雇用時間がないためレコードは追加されませんでした。 " + formatted_start_time)
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                        continue
                    writer.writerow(record)
                except UnicodeEncodeError:
                    # 認識できない文字に対する処理が必要
                    # こんなエラーが出たときに対処
                    # UnicodeEncodeError: 'shift_jisx0213' codec can't encode character '\uff3c' in position 309: illegal multibyte sequence
                    # https://0g0.org/unicode/ff5e/
                    # 〜
                    record = list(map(lambda r: str(r).replace(u"\uff5e", u"\u301c"), record))
                    # https://0g0.org/unicode/2763/
                    # ❣
                    record = list(map(lambda r: str(r).replace(u"\u2763", ""), record))
                    # https://0g0.org/unicode/ff3c/
                    # ＼ > \
                    record = list(map(lambda r: str(r).replace(u"\uff3c", u"\u005c"), record))
                    writer.writerow(record)
                    continue

    # nextにあってsmartにないレコードの処理
    # 非掲載既存求人の処理
    closed_records = []
    with open('csv/next/' + start_time + '/job_' + start_time[:8] + '.csv', 'r', encoding='shift_jisx0213') as next_f:
        next_reader = csv.reader(next_f)
        with open('log/insert_' + start_time + '.log', 'a') as log_f:
            log_f.write("非掲載既存求人の処理\n")
        for next_i, next_row in enumerate(next_reader):
            if next_i == 0 or next_row.__len__() == 0:
                continue
            with open('csv/smart/smart_origin_' + start_time + '.csv', 'r') as smart_f:
                smart_reader = csv.reader(smart_f)
                exist_flag = False
                for smart_i, smart_row in enumerate(smart_reader):
                    if smart_i == 0 or smart_row.__len__() == 0:
                        continue
                    insert_log(start_time, smart_row)
                    if smart_row[0] == next_row[104]:
                        exist_flag = True
                        break
                if exist_flag == False:
                    closed_records.append(next_row)

    with open('csv/trancom/trancom_origin_' + start_time + '.csv', 'a', encoding='shift_jisx0213') as trancom_f:
        writer = csv.writer(trancom_f, lineterminator='\n')
        for closed_record in closed_records:
            insert_log(start_time, closed_record)
            closed_record[2] = datetime.datetime.today().strftime("%Y/%m/%d 00:00")
            writer.writerow(closed_record)

    # nextに上がっているが、まだ取り込まれていないレコードの処理
    records = []
    with open('csv/trancom/trancom_origin_' + start_time + '.csv', 'r', encoding='shift_jisx0213') as trancom_f:
        trancom_reader = csv.reader(trancom_f)
        with open('log/insert_' + start_time + '.log', 'a') as log_f:
            log_f.write("nextのまだ取り込まれていないレコードの処理\n")
        for trancom_i, trancom_row in enumerate(trancom_reader):
            if trancom_i == 0 or trancom_row.__len__() == 0:
                continue
            insert_log(start_time, trancom_row)
            records.append(trancom_row[104])

    # recordsの中にあげる用のcsvの中身が入った
    insert_records = []
    with open('csv/next/' + start_time + '/job_' + start_time[:8] + '.csv', 'r', encoding='shift_jisx0213') as next_f:
        next_reader = csv.reader(next_f)
        with open('log/insert_' + start_time + '.log', 'a') as log_f:
            log_f.write("next_csvの作成\n")
        for next_i, next_row in enumerate(next_reader):
            if next_i == 0 or next_row.__len__() == 0:
                continue
            insert_log(start_time, next_row)
            exist_flag = False
            for record in records:
                if next_row[104] == record:
                    exist_flag = True
            if exist_flag == False:
                insert_records.append(next_row)

    with open('csv/trancom/trancom_origin_' + start_time + '.csv', 'a', encoding='shift_jisx0213') as trancom_f:
        writer = csv.writer(trancom_f, lineterminator='\n')
        with open('log/insert_' + start_time + '.log', 'a') as log_f:
            log_f.write("trancom_csvの作成\n")
        for insert_record in insert_records:
            insert_log(start_time, insert_record)
            writer.writerow(insert_record)

def csv_converter(data, exist_records):
    # smartのデータを読み込んで変換をする
    # !! HeadsUp !!
    # なぜ24列目を追加しているのか意図はわからないが、初期のcommitから存在していて、
    # 多数のカラムに影響するので、残したままにしています。
    data.insert(24, '')
    record = [
        # スプレッドシートの列番号と比較する場合は -1 で見ること（配列の0スタートで記述されているため）
        # スプレッドシートの対応IDも同じく
        '',   # 0 求人情報ID:既存案件は既存の値を入れる 初登録案件は空白
        '',   # 1 公開開始日時:
        '',   # 2 公開終了日時:既存案件で非公開のものは以下を入力 TODAY() 0:00
        '3',  # 3 掲載優先順位: 既存案件は既存の値を入れる 初登録案件は3
        '8',  # 4 求人登録企業ID:
        '株式会社foredge',  # 求人登録企業名:
        'トランコムSC',  # 分類
        catch_copy(data[2], data[3]),  # キャッチコピー: 3,4の内容を職種変換表（2シート目）に合わせて変換し、以下のルールで入力する。[職種詳細1]/[職種詳細2]※ただし、職種詳細2が空白の場合は[職種詳細1]のみの記載
        data[52],  # タイトル: 既存案件は既存の値を入れる。
        '',  #
        '',  # 10 求人掲載企業名
        '',  #
        '',  #
        job_type(data[2], data[3]),  # 職種: 3,4の内容を職種変換表（2シート目）に合わせて変換し、 以下のルールで入力する。 [職種詳細1],[職種詳細2] ※ただし、職種詳細2が空白の場合は[職種詳細1]のみの記載
        temporary_staff(data[4], data[4]),   # 雇用形態 派遣 表示
        temporary_staff(data[4], data[32]),  #
        temporary_staff(data[4], data[33]),  #
        temporary_staff(data[4], ''),  #
        temporary_staff(data[4], data[21]),  #
        contract_employee(data[4], data[4]),   # 雇用形態 請負 表示
        contract_employee(data[4], data[32]),  #
        contract_employee(data[4], data[33]),  #
        contract_employee(data[4], ''),        #
        contract_employee(data[4], data[21]),  #
        placement(data[4], data[4]),   # 雇用形態 職業紹介 表示
        placement(data[4], data[32]),  #
        placement(data[4], data[33]),  #
        placement(data[4], ''),        #
        placement(data[4], data[21]),  #
        contract_to_regular_employee(data[4], data[4]),   # 雇用形態 紹介予定派遣 表示
        contract_to_regular_employee(data[4], data[32]),  #
        contract_to_regular_employee(data[4], data[33]),  #
        contract_to_regular_employee(data[4], ''),        #
        contract_to_regular_employee(data[4], data[21]),  #
        contract_part_employee(data[4], data[4]),   # 雇用形態 契約社員・パート・アルバイト 表示
        contract_part_employee(data[4], data[32]),  # 雇用形態 契約社員・パート・アルバイト 給与単位
        contract_part_employee(data[4], data[33]),  # 雇用形態 契約社員・パート・アルバイト 給与（低）
        contract_part_employee(data[4], ''),        # 雇用形態 契約社員・パート・アルバイト 給与（高）
        contract_part_employee(data[4], data[21]),  # 雇用形態 契約社員・パート・アルバイト 備考
        regular_employee(data[4], data[4]),   # 雇用形態 正社員 表示 5が「正社員」の場合のみ以下を入力 正社員 表示
        regular_employee(data[4], data[32]),  # 雇用形態 正社員 給与単位
        regular_employee(data[4], data[33]),  # 雇用形態 正社員 給与（低）
        regular_employee(data[4], ''),        #
        regular_employee(data[4], data[21]),  # 雇用形態 正社員 備考 5が「正社員」の場合のみ
        data[7],   #
        data[8],   # 勤務地（市区町村）
        '',        # work_area(data[9]),   # 勤務地（住所）# 番地までは表示しなくてもいいためコメントアウト
        '',        # 最寄駅1（路線）
        data[10],  # 最寄駅1（駅名）
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        overwork_time(float(data[35]) + float(data[41]) + float(data[47])),  # 残業 以下のルールで入力する。([36]+[42]+[48])時間程度 ただし、「0時間程度」となる場合は以下を入力する。 原則ありません。
        '',  #
        data[18],  # 休日・休暇
        work_time(data[12], data[13]),  # 勤務時間1（開始時間）
        work_time(data[13], data[12]),  # 勤務時間1（終了時間）
        '',                             # 勤務時間1（備考）
        work_time(data[14], data[15]),  # 勤務時間2（開始時間）
        work_time(data[15], data[14]),  # 勤務時間2（終了時間）
        '',                             # 勤務時間2（終了時間）
        work_time(data[16], data[17]),  # 勤務時間3（開始時間）
        work_time(data[17], data[16]),  # 勤務時間3（終了時間）
        '',                             # 勤務時間3（備考）
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        data[11],  # 86 仕事内容 既存案件は既存の値を入れる
        '',  # 87 ここがポイント 既存案件は既存の値を入れる
        data[22],  # 88 応募資格
        'どちらでも',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        job_type_text(data[2], data[3]),  # 職種（テキスト） 3,4の内容を職種変換表（2シート目）に合わせて変換し、以下のルールで入力する。[職種詳細1][職種詳細2] ※職種詳細1と職種詳細2と2つある場合改行する。
        'trancomsc-center@job-entry.com',  # 問い合わせ先：メールアドレス 規定の内容
        '0120-2525-56',  # 問い合わせ先：電話番号 規定の内容
        '平日 8:30〜18:00　土日祝 9:00〜17:00',  # 問い合わせ先：電話受付時間 規定の内容
        data[0],  # お仕事No. 既存案件かの確認に利用
        '電話でご応募いただく際は【お仕事No：' + data[0] + '】をお伝えください',  # 問い合わせ先：担当者 以下のルールで入力する。 電話でご応募いただく際は【お仕事No.[1]】をお伝えください。
        'trancomsc-center@job-entry.com',  # 応募通知先 規定の内容
        '',  #
        '',  #
        '',  #
        '',  #
        '',  #
        particular_about(data[26]),  # 112 こだわり条件‐入社祝金
        particular_about(data[27]),  #
        particular_about(data[28]),  #
        particular_about(data[29]),  #
        particular_about(data[30]),  #
        particular_about(data[31]),  #
        particular_about(data[55]),  #
        particular_about(data[56]),  #
        particular_about(data[57]),  #
        particular_about(data[58]),  #
        particular_about(data[59]),  #
        particular_about(data[60]),  #
        particular_about(data[61]),  #
        particular_about(data[62]),  #
        particular_about(data[63]),  #
        particular_about(data[64]),  #
        particular_about(data[65]),  #
        particular_about(data[66]),  #
        dormitory_fee(data[66], data[67]),  # 130 こだわり条件‐寮費無料 無料の場合のみ以下を入力 1
        particular_about(data[77]),  # 131 こだわり条件‐未経験OK
        particular_about(data[78]),  # こだわり条件‐男性活躍中
        particular_about(data[79]),  # こだわり条件‐女性活躍中
        particular_about(data[80]),  #
        particular_about(data[81]),  #
        particular_about(data[82]),  #
        particular_about(data[83]),  #
        particular_about(data[84])   # こだわり条件‐大量募集
    ]

    # 既存レコードの場合
    for exist_record in exist_records:
        if record[45] == '上三川町':
            record[45] = '河内郡上三川町'
        if data[0] in exist_record:
            record[0] = exist_record[0]
            record[1] = exist_record[1]
            #record[2] = exist_record[2]
            record[3] = exist_record[3]
            record[7] = exist_record[7]
            record[8] = exist_record[8]
            record[9] = exist_record[9]
            record[86] = exist_record[86]
            record[87] = exist_record[87]
    # 仕事内容にこだわり条件の内容を付与する処理
    record = add_particular_about(record, data)

    return record

def add_particular_about(record, data):
    # 文字列を操作して増減できるようにする
    add_words = ''
    if record[112] == '1':
        add_words += '#入社祝金 '
    if record[113] == '1':
        add_words += '#ミニボーナス '
    if record[114] == '1':
        add_words += '#満了祝金 '
    if record[115] == '1':
        add_words += '#赴任旅費 '
    if record[116] == '1':
        add_words += '#引越費用 '
    if record[117] == '1':
        add_words += '#その他手当 '
    if record[118] == '1':
        add_words += '#高月給 '
    if record[119] == '1':
        add_words += '#交通費支給 '
    if record[120] == '1':
        add_words += '#扶養範囲OK '
    if record[121] == '1':
        add_words += '#マイカー通勤 '
    if record[122] == '1':
        add_words += '#駐車場 '
    if record[123] == '1':
        add_words += '#送迎 '
    if record[124] == '1':
        add_words += '#日勤固定 '
    if record[125] == '1':
        add_words += '#夜勤固定 '
    if record[126] == '1':
        add_words += '#2交替 '
    if record[127] == '1':
        add_words += '#3交替 '
    if record[128] == '1':
        add_words += '#残業休出 '
    if record[129] == '1':
        add_words += '#寮･社宅 '
    if record[130] == '1':
        add_words += '#寮費無料 '
    if record[131] == '1':
        add_words += '#未経験OK '
    if record[132] == '1':
        add_words += '#男性活躍中 '
    if record[133] == '1':
        add_words += '#女性活躍中 '
    if record[134] == '1':
        add_words += '#シニア活躍中 '
    if record[135] == '1':
        add_words += '#ペア･家族OK '
    if record[136] == '1':
        add_words += '#資格スキルサポート '
    if record[137] == '1':
        add_words += '#オープニング '
    if record[138] == '1':
        add_words += '#大量募集 '

    if record[86].find('\n\n\n...') != -1:
        record[86] = record[86].split('\n\n\n...')[0]

    record[86] += '\n\n\n...'
    record[86] += add_words

    # 受動喫煙対策の文言をタグの下に挿入
    record[86] += passive_smoking(data[85], data[87])

    return record

def temporary_staff(employee_type, data):
    if employee_type == '派遣':
        if data == '派遣':
            return '派遣 表示'
        return data
    return ''

def contract_employee(employee_type, data):
    if employee_type == '請負':
        if data == '請負':
            return '請負 表示'
        return data
    return ''

def contract_part_employee(employee_type, data):
    if employee_type == '契約・パート・アルバイト':
        if data == '契約・パート・アルバイト':
            return '契約・パート・アルバイト 表示'
        return data
    return ''

def regular_employee(employee_type, data):
    if employee_type == '正社員':
        if data == '正社員':
            return '正社員 表示'
        return data
    return ''

def contract_to_regular_employee(employee_type, data):
    if employee_type == '紹介予定派遣':
        if data == '紹介予定派遣':
            return '紹介予定派遣 表示'
        return data
    return ''

def placement(employee_type, data):
    if employee_type == '職業紹介':
        if data == '職業紹介':
            return '職業紹介 表示'
        return data
    return ''

def work_area(data):
    if data == '以下に掲載がない場合':
        return ''
    return data

def overwork_time(data):
    if data == 0:
        return '原則ありません'
    return str(round(data)) + '時間程度'

def passive_smoking(data1, data2):
    if data1 == 'あり':
        return '\n\n' + '受動喫煙防止対策：あり\n' + data2
    return ''

def work_time(base_time, compare_time):
    if base_time == '00:00' and compare_time == '00:00':
        return ''
    return base_time

def particular_about(data):
    if data == '' or data == '0' or data == '0\n':
        return ''
    return '1'

def catch_copy(data1, data2):
    change_data1 = JOB_CONVERT_RULE.get(data1)
    change_data2 = JOB_CONVERT_RULE.get(data2)
    if change_data1 is None:
        return ''
    elif change_data2 is None:
        return change_data1
    else:
        return change_data1 + '/' + change_data2

def job_type(data1, data2):
    change_data1 = JOB_CONVERT_RULE.get(data1)
    change_data2 = JOB_CONVERT_RULE.get(data2)
    if change_data1 is None:
        return ''
    elif change_data2 is None:
        return change_data1
    else:
        return change_data1 + ',' + change_data2

def job_type_text(data1, data2):
    change_data1 = JOB_CONVERT_RULE.get(data1)
    change_data2 = JOB_CONVERT_RULE.get(data2)
    if change_data1 is None:
        return ''
    elif change_data2 is None:
        return change_data1
    else:
        return change_data1 + '\n' + change_data2

def dormitory_fee(dormitory, dormitory_fee):
    if dormitory == '1' and dormitory_fee == '無料':
        return 1
    return ''

def g_drive_upload(folder_id, remote_file_name, local_file_path):
    if os.path.exists(local_file_path):
        try:
            gauth = GoogleAuth()
            gauth.CommandLineAuth()
            drive = GoogleDrive(gauth)

            f = drive.CreateFile({'title': remote_file_name,
                                'mimeType': 'text/plain',
                                'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
            f.SetContentFile(local_file_path)
            f.Upload()
            print('Successfully upload file ' + local_file_path)
        except:
            print('Failed to upload file ' + local_file_path)

def get_job_convert_rule():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./spreadsheet_service_account.json', scope)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(os.environ['SPREADSHEET_KEY']).sheet1
    before = worksheet.col_values(1)
    after = worksheet.col_values(2)
    return dict(zip(before, after))

def insert_log(start_time, row):
    with open('log/insert_' + start_time + '.log', 'a') as log_f:
        for i, record in enumerate(row):
            log_f.write("'" + record + "'")
            if i != len(row) - 1:
                log_f.write(",")

# GCSにファイルアップロードして削除
def upload_file_to_gcs(start_time):
    local_file_name = "unsent_recruit_" + start_time + ".log"
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
    # start_time = '20201027103945'
    try:
        global JOB_CONVERT_RULE
        JOB_CONVERT_RULE = get_job_convert_rule()
        print('csv_download_from_next')
        csv_download_from_next(start_time)
        print('csv_download_from_smart')
        csv_download_from_smart(start_time)
        print('csv_make_for_trancom')
        csv_make_for_trancom(start_time)
        print('csv_upload')
        csv_upload_to_410510(start_time)
        print('upload_file_to_gcs')
        upload_file_to_gcs(start_time)
        print('g_drive_upload files')
        g_drive_upload(
            '1ROwxoJrX03sNGHqv6j5EYCpTMaiMwGY5',
            'job_' + start_time[:8] + '.csv',
            'csv/next/' + start_time + '/job_' + start_time[:8] + '.csv'
        )
        g_drive_upload(
            '1rpH5o5wOAGL8WdMPS8kObPzcFL1rCrTf',
            'smart_origin_' + start_time + '.csv',
            'csv/smart/smart_origin_' + start_time + '.csv'
        )
        g_drive_upload(
            '1xEhxdRAY34EzY6W2teNMmu0VX5Sr5IPK',
            'trancom_origin_' + start_time + '.csv',
            'csv/trancom/trancom_origin_' + start_time + '.csv'
        )
        g_drive_upload(
            os.environ['GDRIVE_FOLDER_ID'],
            start_time + '_log.csv',
            'log/unsent_recruit_' + start_time + '.log'
        )
        print('All process completed')
        return f'ok!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    except:
        subject = 'トランコム自動アップロードのスクリプトが異常終了しました'
        body = 'プログラムの実行時にエラーが発生しました。システム管理者にご報告ください。'
        print(traceback.format_exc())
        send_mail(os.environ['FROM_ADDRESS'], os.environ['TO_ADDRESS'], subject, body)
        send_slack(subject + "\n" + traceback.format_exc())
        return f'Except!!'

if __name__ == "__main__":
    main()
