# EDINETの情報取得スクリプト

## 実行方法

### docker imageのビルド

```bash
./build.sh
```

### docker runで実行

- 期間は環境変数で指定する
  - from: 検索対象の開始日
  - to: 検索対象の終了日
- 環境変数で期間の指定がない場合は、会計年度中のものを対象とする
  - 実行が4月〜12月の場合、当年の4月1日〜当年の今日までを取得
  - 実行が1月〜3月の場合、昨年の4月〜当年の今日までを取得
- CSV出力する場合
  - `-e mode=csv` を設定
  - /tmp/にdocument_list.csvを出力するので、 -v /tmp:/tmp でホスト側に出力させるようにする

```bash
docker run --rm -it -v $(pwd)/app:/app -v /tmp:/tmp -e from=2022-11-18 -e to=2022-11-20 -e mode=csv edinet-search
```

### UnitTestの実行

```bash
docker run --rm -it -v $(pwd)/app:/app -v $(pwd)/tests:/tests edinet-search python -m unittest tests.test_edinet
```