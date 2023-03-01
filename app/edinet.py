from edinet_xbrl.edinet_xbrl_parser import EdinetXbrlParser
import zipfile
import requests
import glob
import os
import re
import shutil
import datetime
from dateutil import relativedelta
import yaml
import time
import csv

class Edinet:
    """
    EDINET APIを扱うクラス.
    """

    # EDINET API
    ## 書類一覧API
    API_DOC_LIST_JSON = "https://disclosure.edinet-fsa.go.jp/api/v1/documents.json"
    ## 書類取得API
    API_GET_DOC_BASE = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/"
    ## 府令コード（企業内容等の開示に関する内閣府令）
    ORDINANCE_CODE = "010"
    ## 様式コード（第三号様式 有価証券報告書）
    FORM_CODE = "030000"

    # 処理件数
    PROCESS_NUM = 50

    def __init__(self) -> None:
        today = datetime.date.today()
        if datetime.date.today().month < 4:
            # 1-3月はFYのため前の年を取得
            start_year = (today + relativedelta.relativedelta(years=-1)).year
        else:
            start_year = today.year

        self.start_date = datetime.date(start_year, 4, 1)
        self.end_date = datetime.date(today.year, today.month, today.day)

    def set_target_term(self, target_start_date: datetime, target_end_date: datetime) -> None:
        """
        書類一覧取得の対象期間を指定する.
        Args:
            target_start_date: datetime
            target_end_date: datetime
        Returns:
            None
        """
        self.start_date = target_start_date
        self.end_date = target_end_date

    def __make_day_list(self) -> list:
        """
        対象日付リストの作成.
        Returns:
            day_list: list : 取得対象日のdatetimeオブジェクトの配列
        """
        print("start_date：", self.start_date)
        print("end_day：", self.end_date)

        period = self.end_date - self.start_date
        period = int(period.days)
        day_list = []
        for d in range(period):
            day = self.start_date + datetime.timedelta(days=d)
            day_list.append(day)

        day_list.append(self.end_date)

        return day_list

    def get_document_list(self) -> list:
        """
        書類リスト検索を行う.
        Returns:
            doc_list: list : 有価証券報告書リスト
        """
        day_list = self.__make_day_list()
        doc_list = self.__search_document(day_list)
        return doc_list

    def get_document_data(self) -> None:
        """
        書類データを取得しcsvファイルの書き出し行う.
        処理対象書類が多いことを考慮し、書類取得をしたら PROCESS_NUM 件ずつ処理してCSV書き出しを行う
        Return:
            None
        """
        doc_list = self.get_document_list()
        xbrl_data_list = []
        dest_file = '/tmp/document_list.csv'

        if os.path.isfile(dest_file):
            print('すでにファイル' + dest_file + 'が存在しています.')
            return

        with open('/app/configs/layout.yaml') as layout:
            layout_data = yaml.safe_load(layout)

        with open(dest_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, layout_data['HEADER'])
            writer.writeheader()

        print(str(len(doc_list)) + '件のダウンロードとCSV出力をします.')
        while len(doc_list) > 0:
            doc = doc_list.pop()
            filename = self.__download_xbrl(doc['docID'])
            xbrl_data = self.__parse_xbrl(filename, doc)
            xbrl_data_list.append(xbrl_data)

            if len(xbrl_data_list) == self.PROCESS_NUM:
                print(str(len(xbrl_data_list)) + '件書き込みします.')
                for xbrl_dic in xbrl_data_list:
                    with open(dest_file, 'a', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, layout_data['HEADER'])
                        writer.writerow(xbrl_dic)
                xbrl_data_list = []
                time.sleep(5)

        if len(xbrl_data_list) > 0:
            for xbrl_dic in xbrl_data_list:
                with open(dest_file, 'a', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, layout_data['HEADER'])
                    writer.writerow(xbrl_dic)

        print('csv出力完了.')

    def __search_document(self, day_list: list) -> list:
        """
        書類リスト検索APIの実行.
        Args:
            day_list: list : 対象日リスト
        Returns:
            doc_list: list : 有価証券報告書docIdリスト
        """
        doc_list = []
        for index, day in enumerate(day_list):
            # HTTP 403が返ってくることがあるので5回までリトライする
            for _ in range(5):
                params = {"date": day, "type": 2}
                res = requests.get(self.API_DOC_LIST_JSON, params=params)
                if res.status_code != 200:
                    print(day)
                    print('HTTPステータスコード:' + str(res.status_code) + ' 10秒スリープします')
                    time.sleep(10)
                    continue
                else:
                    break

            json_data = res.json()

            for num in range(len(json_data["results"])):
                ordinance_code = json_data["results"][num]["ordinanceCode"]
                form_code = json_data["results"][num]["formCode"]
                if ordinance_code == self.ORDINANCE_CODE and form_code == self.FORM_CODE:
                    doc_list.append(json_data["results"][num])
            if index % 10 == 0:
                # API負荷対策で10回に2秒スリープする
                time.sleep(2)

        return doc_list

    def __download_xbrl(self, doc_id: str) -> str:
        """
        XBRLファイルのダウンロードを実行する.
        Args:
            doc_id: str : 有価証券報告書docID
        Returns:
            filename: str : ダウンロードしたファイル名
        """
        url = self.API_GET_DOC_BASE + doc_id
        params = {"type": 1}
        filename = "/tmp/" + doc_id + ".zip"

        # リトライ処理(5回まで)
        for _ in range(5):
            res = requests.get(url, params=params, stream=True)
            if res.status_code != 200:
                print('HTTPステータスコード:' + str(res.status_code) + ' 10秒スリープします')
                time.sleep(10)
                continue
            else:
                break

        with open(filename, 'wb') as file:
            for chunk in res.iter_content(chunk_size=1024):
                file.write(chunk)

        return filename

    def __parse_xbrl(self, filename: str, doc: dict) -> dict:
        """
        XBRLファイルの解析し、必要なデータを取得する.
        Args:
            doc: dic : ダウンロードしたzipファイルのパスリスト
        Returns:
            xbrl_data: list : 必要な項目のデータの辞書群の配列.
        """
        with open('/app/configs/layout.yaml', 'rb') as layout:
            layout_data = yaml.safe_load(layout)

        doc_id = doc['docID']
        unzipPath = '/tmp/' + doc_id + '/'
        with zipfile.ZipFile(filename, 'r') as z:
            z.extractall(unzipPath)
        
        xbrlfiles = glob.glob(unzipPath + 'XBRL/PublicDoc/*.xbrl')

        parser = EdinetXbrlParser()
        xbrl_obj = parser.parse_file(xbrlfiles[0])

        data_dic = {}
        data_dic[layout_data['EXTRA_TARGET']['SEC_CODE']] = doc['secCode']

        for field in layout_data['TARGET']:
            if xbrl_obj.get_data_by_context_ref(field['KEY'], field['CONTEXT_ID']):
                data_dic[field['NAME']] = xbrl_obj.get_data_by_context_ref(field['KEY'], field['CONTEXT_ID']).get_value()
            if field['NAME'] not in data_dic:
                data_dic[field['NAME']] = ''

        shutil.rmtree(unzipPath)
        os.remove(filename)
        return data_dic
