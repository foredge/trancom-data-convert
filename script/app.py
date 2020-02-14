# coding: UTF-8
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from time import sleep
import datetime
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
from flask import Flask

JOB_CONVERT_RULE = {}
FROM_ADDRESS = os.environ['FROM_ADDRESS']
MY_PASSWORD = os.environ['MY_PASSWORD']
TO_ADDRESS = os.environ['TO_ADDRESS']
BCC = ''
SUBJECT = 'トランコム自動アップロードが失敗しました。'
BODY = ''

app = Flask(__name__)

def send_mail(from_addr, to_addrs, subject, body):
    return requests.post(
        "https://api.mailgun.net/v3/" + os.environ['MAIL_DOMAIN'] + "/messages",
        auth=("api", os.environ['MAILGUN_API_KEY']),
        data={"from": from_addr,
              "to": to_addrs,
              "subject": subject,
              "text": body})

def send_error_mail(text):
    to_addr = TO_ADDRESS
    subject = SUBJECT
    body = text

    msg = create_message(FROM_ADDRESS, to_addr, BCC, subject, body)
    send(FROM_ADDRESS, to_addr, msg)


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


def csv_upload(start_time):
    print('csv_upload')
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--window-size=1366,768')

    driver = webdriver.Chrome(chrome_options=options)
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
    driver = webdriver.Chrome(chrome_options=options)
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
    download_file_path = "./csv/next/job_" + start_time[:8] + ".csv"
    sleep(10)
    driver.close()
    driver.quit()


def download_curl_to_smart(start_time):
    os.system("curl -c " + os.getcwd() + "/cookie.txt" + " -d " + os.environ['COOKIEBODY'] + " -x http://" + os.environ['PROXY_SERVER']  + ":80 -k 'http://talent.metastasys.biz/sinfoniacloud/api/Login.json'"
                                                         " -H 'Origin: https://talent.metastasys.biz'"
                                                         " -H 'Accept-Encoding: gzip, deflate, br'"
                                                         " -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8'"
                                                         " -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'"
                                                         " -H 'Content-Type: application/json'"
                                                         " -H 'Accept: application/json, text/javascript, */*; q=0.01'"
                                                         " -H 'Referer: https://talent.metastasys.biz/appl/menu.html'"
                                                         " -H 'X-Requested-With: XMLHttpRequest'"
                                                         " -H 'Connection: keep-alive'"
                                                         " --compressed")

    curl_data = subprocess.Popen(["curl -b " + os.getcwd() + "/cookie.txt" + " -x http://" + os.environ['PROXY_SERVER'] + ":80 -k 'http://talent.metastasys.biz/sinfoniacloud/api/GetJobCaseReferListRESTFacade.json"
                                                                            "?_qt=false&_limitCount=2000&jobNo=&jobOffersName_Like=&customerCode=&prefectures_Like=&cityName_Like=&organizationCode=&personResponsibleCode=&jobCategory=&ageTo=&gender=&predeterminedAllowance_hour=&predeterminedAllowance_month=&paymentClassification=&predeterminedAllowance_From=&holidayPossible_Like=&workDayWeekHolidayCondition_In=&necessaryQualifications=&mediumSupplierCode=&contractForm=&proposalRankType=&hiringRank=&postClassified=%E6%8E%B2%E8%BC%89%E4%B8%AD&dormitoriesCompanyHousing=0&foreignerPropriety=0&tattooPropriety=0&historyRefer=0&approvalClassification_IN=%E6%89%BF%E8%AA%8D%E6%B8%88&applicationClassification=&orderClassification=&priorityRank=&orderRemainingNumberPeople_From=&orderRemainingNumberPeople_To=&predeterminedAllowance=&jobRecruitmentStartDate=&jobRecruitmentEndDate=&assignedDueDate_From=&assignedDueDate_To=&workingPeriod=&nearestStation_Like=&jobDetails=&prefecturesKana_Like=&cityNameKana_Like=&approvalStateClassification=%E6%9C%80%E7%B5%82%E6%89%BF%E8%AA%8D&_=1533794896192'"
                                                                            " -H 'Accept-Encoding: gzip, deflate, br'"
                                                                            " -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8'"
                                                                            " -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'"
                                                                            " -H 'Accept: application/json, text/javascript, */*; q=0.01' "
                                                                            " -H 'Referer: https://talent.metastasys.biz/appl/html/jobOffers/JobCaseRefer.html'"
                                                                            " -H 'X-Requested-With: XMLHttpRequest' "
                                                                            " -H 'Connection: keep-alive'"
                                                                            " --compressed"], stdout=subprocess.PIPE, shell=True).stdout.read()
    return curl_data

def csv_download_from_smart(start_time):
    print('smartのcsvをダウンロード')
    with open('csv/smart/smart_origin_' + start_time + '.csv', 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow('お仕事No,職種,職種詳細1,職種詳細2,雇用形態,営業所,担当者,都道府県,市区町村,住所詳細,最寄駅,お仕事内容,シフト１・開始時刻,シフト１・終了時刻,シフト２・開始時刻,シフト２・終了時刻,シフト３・開始時刻,シフト３・終了時刻,休日,勤務シフト,休日･シフト備考,月収例,応募条件,必要資格,必要資格2,給与見込額,入社祝金,ミニボーナス,満了祝金,赴任旅費,引越費用,その他手当,給与単位,所定(円),シフト１・所定(日),シフト１・残業(H),シフト１・開始時刻,シフト１・終了時刻,シフト１・実働(H),シフト１・休憩時間(M),シフト２・所定(日),シフト２・残業(H),シフト２・開始時刻,シフト２・終了時刻,シフト２・実働(H),シフト２・休憩時間(M),シフト３・所定(日),シフト３・残業(H),シフト３・開始時刻,シフト３・終了時刻,シフト３・実働(H),シフト３・休憩時間(M),見出し,入社まで期間,高時給,高月給,交通費支給,扶養範囲OK,マイカー通勤,駐車場,送迎,日勤固定,夜勤固定,2交替,3交替,残業休出,寮･社宅,寮費,入寮期間,間取り,通勤距離,水道光熱,家電設備,築年数,駐車場,最寄駅,商業施設,未経験OK,男性活躍中,女性活躍中,シニア活躍中,ペア･家族OK,資格スキルサポート,オープニング,大量募集'.split(','))

    records = json.loads(download_curl_to_smart(start_time))
    for i, record in enumerate(records['body']['_obj0']):
        req_record = "%7B" \
                 "%22dummy3%22%3A%22%E5%B1%A5%E6%AD%B4%22%2C" \
                 "%22approvalClassification%22%3A%22" + urllib.parse.quote(record['approvalClassification']) + "%22%2C" \
                 "%22applicationClassification%22%3A%22" + urllib.parse.quote(record['applicationClassification']) + "%22%2C" \
                 "%22jobNo%22%3A%22" + urllib.parse.quote(record['jobNo']) + "%22%2C" \
                 "%22customerCode%22%3A%22" + urllib.parse.quote(record['customerCode']) + "%22%2C" \
                 "%22customerName%22%3A%22" + urllib.parse.quote(record['customerName']) + "%22%2C" \
                 "%22jobOffersName%22%3A%22" + urllib.parse.quote(record['jobOffersName']) + "%22%2C" \
                 "%22organizationCode%22%3A%22" + urllib.parse.quote(record['organizationCode']) + "%22%2C" \
                 "%22organizationName%22%3A%22" + urllib.parse.quote(record['organizationName']) + "%22%2C" \
                 "%22orderAmount%22%3A%22" + urllib.parse.quote(record['orderAmount']) + "%22%2C" \
                 "%22assignedDueDate%22%3A%22" + urllib.parse.quote(record['assignedDueDate']) + "%22%2C" \
                 "%22orderRemainingNumberPeople%22%3A%22" + urllib.parse.quote(record['orderRemainingNumberPeople']) + "%22%2C" \
                 "%22receptionNumberPeople%22%3A" + urllib.parse.quote(str(record['receptionNumberPeople'])) + "%2C" \
                 "%22numberPeopleMatching%22%3A" + urllib.parse.quote(str(record['numberPeopleMatching'])) + "%2C" \
                 "%22adoptedNumberPeople%22%3A" + urllib.parse.quote(str(record['adoptedNumberPeople'])) + "%2C" \
                 "%22notAdoptedNumberPeople%22%3A" + urllib.parse.quote(str(record['notAdoptedNumberPeople'])) + "%2C" \
                 "%22createdate_begin%22%3A%22" + urllib.parse.quote(record['createdate_begin']) + "%22%2C" \
                 "%22createtime_begin%22%3A%22" + urllib.parse.quote(record['createtime_begin']) + "%22%2C" \
                 "%22comment%22%3A%22" + urllib.parse.quote("") + "%22%2C" \
                 "%22approvalComments%22%3A%22" + urllib.parse.quote(record['approvalComments']) + "%22%2C" \
                 "%22holdDenialReason%22%3A%22" + urllib.parse.quote(record['holdDenialReason']) + "%22%2C" \
                 "%22createdate_pre%22%3A%22" + urllib.parse.quote(record['createdate_pre']) + "%22%2C" \
                 "%22createtime_pre%22%3A%22" + urllib.parse.quote(record['createtime_pre']) + "%22%2C" \
                 "%22createdate_end%22%3A%22" + urllib.parse.quote(record['createdate_end']) + "%22%2C" \
                 "%22createtime_end%22%3A%22" + urllib.parse.quote(record['createtime_end']) + "%22%2C" \
                 "%22prefectures1%22%3A%22" + urllib.parse.quote(record['prefectures1']) + "%22%2C" \
                 "%22cityName1%22%3A%22" + urllib.parse.quote(record['cityName1']) + "%22%2C" \
                 "%22personResponsibleCode%22%3A%22" + urllib.parse.quote(record['personResponsibleCode']) + "%22%2C" \
                 "%22personResponsibleName%22%3A%22" + urllib.parse.quote(record['personResponsibleName']) + "%22%2C" \
                 "%22jobCategory%22%3A%22" + urllib.parse.quote(record['jobCategory']) + "%22%2C" \
                 "%22ageTo%22%3A%22" + urllib.parse.quote(record['ageTo']) + "%22%2C" \
                 "%22gender%22%3A%22" + urllib.parse.quote(record['gender']) + "%22%2C" \
                 "%22paymentClassification%22%3A%22" + urllib.parse.quote(record['paymentClassification']) + "%22%2C" \
                 "%22predeterminedAllowance%22%3A%22" + urllib.parse.quote(record['predeterminedAllowance']) + "%22%2C" \
                 "%22estimatedSalary%22%3A%22" + urllib.parse.quote(record['estimatedSalary']) + "%22%2C" \
                 "%22holidayPossible%22%3A%22" + urllib.parse.quote(record['holidayPossible']) + "%22%2C" \
                 "%22workDayWeekHolidayCondition%22%3A%22" + urllib.parse.quote(record['workDayWeekHolidayCondition']) + "%22%2C" \
                 "%22necessaryQualifications%22%3A%22" + urllib.parse.quote(record['necessaryQualifications']) + "%22%2C" \
                 "%22contractForm%22%3A%22" + urllib.parse.quote(record['contractForm']) + "%22%2C" \
                 "%22proposalRankType%22%3A%22" + urllib.parse.quote(record['proposalRankType']) + "%22%2C" \
                 "%22hiringRank%22%3A%22" + urllib.parse.quote(record['hiringRank']) + "%22%2C" \
                 "%22postClassified%22%3A%22" + urllib.parse.quote(record['postClassified']) + "%22%2C" \
                 "%22dormitoriesCompanyHousing%22%3A%22" + urllib.parse.quote(record['dormitoriesCompanyHousing']) + "%22%2C" \
                 "%22foreignerPropriety%22%3A%22" + urllib.parse.quote(record['foreignerPropriety']) + "%22%2C" \
                 "%22tattooPropriety%22%3A%22" + urllib.parse.quote(record['tattooPropriety']) + "%22%2C" \
                 "%22requestNo%22%3A%22" + urllib.parse.quote(record['requestNo']) + "%22%2C" \
                 "%22orderNo%22%3A%22" + urllib.parse.quote(record['orderNo']) + "%22%2C" \
                 "%22jobProposalNumber%22%3A%22" + urllib.parse.quote(record['jobProposalNumber']) + "%22" \
                 "%7D%2C"

        next_records = subprocess.Popen(["curl -b " + os.getcwd() + "/cookie.txt" \
                               " -x http://" + os.environ['PROXY_SERVER'] + ":80 -k 'http://talent.metastasys.biz/sinfoniacloud/api/GetjobOffersInfomationCsvRESTFacade.json'" \
                               " -H 'Connection: keep-alive' " \
                               " -H 'Cache-Control: max-age=0' " \
                               " -H 'Origin: https://talent.metastasys.biz' " \
                               " -H 'Upgrade-Insecure-Requests: 1' " \
                               " -H 'Content-Type: application/x-www-form-urlencoded' " \
                               " -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36' " \
                               " -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' " \
                               " -H 'Referer: https://talent.metastasys.biz/appl/html/jobOffers/JobCaseRefer.html' " \
                               " -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: ja,en-US;q=0.9,en;q=0.8' " \
                               " --data " \
                               "'_responseType=RedirectIfError" \
                               "&_ns=" \
                               "&_qt=false" \
                               "&_body=%7B%22" \
                               "_obj0%22%3A%5B" + req_record + \
                               "%5D%7D'" \
                               "--compressed"],stdout=subprocess.PIPE, shell=True).stdout.read().decode('utf-8').split('\n', 1)

        # リクエストをした後にエラーが帰ってきた場合
        # 4/18, 19に2699-0006が上がってこなかった件の調査
        # しかし4/22の時点で該当案件が引っかからなくなってしまった
        if 'errorInfo' in next_records[0]:
            with open('log/unsent_recruit_' + start_time + '.log', 'a') as log_f:
                log_f.write("お仕事No: " + urllib.parse.quote(record['jobNo']))
                log_f.write("\r\n")
                log_f.write("smartから求人を取得することができなかったため追加されませんでした。")
                log_f.write("\r\n")
                log_f.write("\r\n")


        with open('csv/smart/smart_origin_' + start_time + '.csv', 'a') as f:
            insert_record = []
            for index, next_record in enumerate(next_records):
                if index == 0:
                    continue
                if next_record == '':
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
                if (i == 0):
                    continue
                if (row.__len__() == 0):
                    continue
                try:
                    insert_log(start_time, row)
                    record = csv_converter(row, exist_records)
                    # 見出し、職種が空の場合レコードを追加しない
                    if record[7] == '' or record[13] == '' or record[62] == '':
                        with open('log/unsent_recruit_' + start_time + '.log', 'a') as log_f:
                            log_f.write("お仕事No: " + row[0])
                            log_f.write("\r\n")
                            if record[7] == '':
                                log_f.write("見出しが空のためレコードは追加されませんでした。")
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                            if record[13] == '':
                                log_f.write("職種詳細1: " + row[2])
                                log_f.write("\r\n")
                                log_f.write("職種詳細2: " + row[3])
                                log_f.write("\r\n")
                                log_f.write("職種変換表にないためレコードは追加されませんでした。")
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                            if record[62] == '':
                                log_f.write("雇用時間がないためレコードは追加されませんでした。")
                                log_f.write("\r\n")
                                log_f.write("\r\n")
                        continue
                    writer.writerow(record)
                except UnicodeEncodeError:
                    # 認識できない文字に対する処理が必要
                    record = list(map(lambda r: str(r).replace(u"\uff5e", u"\u301c"), record))
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
            if (next_i == 0):
                continue
            if (next_row.__len__() == 0):
                continue
            with open('csv/smart/smart_origin_' + start_time + '.csv', 'r') as smart_f:
                smart_reader = csv.reader(smart_f)
                exist_flag = False
                for smart_i, smart_row in enumerate(smart_reader):
                    if (smart_i == 0):
                        continue
                    if (smart_row.__len__() == 0):
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
            if (trancom_i == 0):
                continue
            if (trancom_row.__len__() == 0):
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
            if (next_i == 0):
                continue
            if (next_row.__len__() == 0):
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
    if data.__len__() == 84:
        data.insert(24, '')
    record = [
        '',   # 求人情報ID:既存案件は既存の値を入れる 初登録案件は空白
        '',   # 公開開始日時:
        '',   # 公開終了日時:既存案件で非公開のものは以下を入力 TODAY() 0:00
        '3',  # 掲載優先順位: 既存案件は既存の値を入れる 初登録案件は3
        '8',  # 求人登録企業ID:
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
        data[8],   #
        '',        # work_area(data[9]),   # 勤務地（住所）# 番地までは表示しなくてもいいためコメントアウト
        '',        #
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
        '',        # 勤務時間1（備考）
        work_time(data[14], data[15]),  # 勤務時間2（開始時間）
        work_time(data[15], data[14]),  # 勤務時間2（終了時間）
        '',        # 勤務時間2（終了時間）
        work_time(data[16], data[17]),  # 勤務時間3（開始時間）
        work_time(data[17], data[16]),  # 勤務時間3（終了時間）
        '',        # 勤務時間3（備考）
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
        particular_about(data[26]),  # こだわり条件‐入社祝金
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
        dormitory(data[67]),  # こだわり条件‐寮費無料 無料の場合のみ以下を入力 1
        particular_about(data[77]),  # こだわり条件‐未経験OK
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
    record = add_particular_about(record)

    return record

def add_particular_about(record):
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

def dormitory(data):
    if data == '無料':
        return 1
    return ''

def g_drive_upload_next(start_time):
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    drive = GoogleDrive(gauth)

    folder_id = '1ROwxoJrX03sNGHqv6j5EYCpTMaiMwGY5'
    f = drive.CreateFile({'title': 'job_' + start_time[:8] + '.csv',
                          'mimeType': 'text/plain',
                          'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
    f.SetContentFile('csv/next/' + start_time + '/job_' + start_time[:8] + '.csv')
    f.Upload()

def g_drive_upload_smart(start_time):
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    drive = GoogleDrive(gauth)

    folder_id = '1rpH5o5wOAGL8WdMPS8kObPzcFL1rCrTf'
    f = drive.CreateFile({'title': 'smart_origin_' + start_time + '.csv',
                          'mimeType': 'text/plain',
                          'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
    f.SetContentFile('csv/smart/smart_origin_' + start_time + '.csv')
    f.Upload()

def g_drive_upload_trancom(start_time):
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    drive = GoogleDrive(gauth)

    folder_id = '1xEhxdRAY34EzY6W2teNMmu0VX5Sr5IPK'
    f = drive.CreateFile({'title': 'trancom_origin_' + start_time + '.csv',
                          'mimeType': 'text/plain',
                          'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
    f.SetContentFile('csv/trancom/trancom_origin_' + start_time + '.csv')
    f.Upload()

def g_drive_upload_log(start_time):
    if os.path.exists('./log/unsent_recruit_' + start_time + '.log'):
        gauth = GoogleAuth()
        gauth.CommandLineAuth()
        drive = GoogleDrive(gauth)

        folder_id = '1KIjOxPfZRIeLNs_wadmMQz3QE6IMjmCH'
        f = drive.CreateFile({'title': start_time + '_log.csv',
                              'mimeType': 'text/plain',
                              'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
        f.SetContentFile('log/unsent_recruit_' + start_time + '.log')
        f.Upload()

def get_job_convert_rule():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./Foredge-025d2142fa5c.json', scope)
    gc = gspread.authorize(credentials)
    SPREADSHEET_KEY = os.environ['SPREADSHEET_KEY']
    worksheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
    before = worksheet.col_values(1)
    after = worksheet.col_values(2)
    return dict(zip(before, after))

def insert_log(start_time, row):
    with open('log/insert_' + start_time + '.log', 'a') as log_f:
        for i, record in enumerate(row):
            log_f.write("'" + record + "'")
            if i != len(row) - 1:
                log_f.write(",")

@app.route('/')
def main():
    try:
        global JOB_CONVERT_RULE
        JOB_CONVERT_RULE = get_job_convert_rule()
        start_time = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
        print('csv_download_from_next')
        csv_download_from_next(start_time)
        print('csv_download_from_smart')
        csv_download_from_smart(start_time)
        csv_make_for_trancom(start_time)
        g_drive_upload_next(start_time)
        g_drive_upload_smart(start_time)
        g_drive_upload_trancom(start_time)
        g_drive_upload_log(start_time)
        csv_upload(start_time)
        print('completed')
        return f'ok!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    except:
        subject = 'トランコム自動アップロードのスクリプトが異常終了しました'
        body = 'プログラムの実行時にエラーが発生しました。システム管理者にご報告ください。'
        
        msg = create_message(FROM_ADDRESS, TO_ADDRESS, BCC, subject, body)
        send(FROM_ADDRESS, TO_ADDRESS, msg)
        
        requests.post('https://hooks.slack.com/services/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', data=json.dumps({
            'text': subject + "\n" + traceback.format_exc(),
            'username': u'trancom',
            'icon_emoji': u':ghost:',
            'link_names': 1,
        }))
        return f'Except!!'

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(8000))
