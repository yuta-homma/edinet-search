from edinet import Edinet
import datetime
from datetime import timezone, timedelta
import pprint
import os
from memory_profiler import profile
import gc

@profile
def main():
    JST = timezone(timedelta(hours=+9), 'JST')
    print('[書類取得処理 開始] ' + datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S'))
    edinet = Edinet()
    # 対象期間指定があれば環境変数から受け取る
    if os.getenv('from') and os.getenv('to'):
        start = os.getenv('from').split('-')
        end = os.getenv('to').split('-')

        start_date = datetime.date(int(start[0]), int(start[1]), int(start[2]))
        end_date = datetime.date(int(end[0]), int(end[1]), int(end[2]))
        edinet.set_target_term(start_date, end_date)

    if os.getenv('mode') and os.getenv('mode') == 'csv':
        print('書類取得とCSV書き込みを行います.')
        edinet.get_document_data()
    else:
        print('書類検索のみ実行します.')
        doc_list = edinet.get_document_list()
        print('対象は' + str(len(doc_list)) + '件ありました.')
        del doc_list
    gc.collect()

    print('[書類取得処理 終了] ' + datetime.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == "__main__":
    main()
