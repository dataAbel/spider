import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import time
from retrying import retry
import csv
from fake_useragent import UserAgent
import multiprocessing
import jsonpath
import json
import pymysql
import pymongo
import sqlalchemy
from lxml import etree
import os
# fiddler抓包获取Ajax加载的真实地址
# 代码放到github，注意数据库的密码泄露，同步仓库


url_base = 'https://movie.douban.com/top250?start='
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}

HOST = 'localhost'
USERNAME = 'root'
PASSWD = input('Please input your password:')    
PORT = 3306
DB = 'abel'
TABLE = 'douBanMovieTop250'


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


# 处理正则表达式无法匹配时，调用group方法报错
def none_group(string):
    if not string:
        return str(string).strip()
    else:
        return 'Null'


@retry(stop_max_attempt_number=5)
def page_source(url):
    retry_count = 5
    proxy = get_proxy().get("proxy")
    headers = {'User-Agent': UserAgent().chrome}
    while retry_count > 0:
        try:
            html = requests.get(url, proxies={"http": "http://{}".format(proxy)}, headers=headers, timeout=(40, 30))
            # 使用代理访问
            if html.status_code == 200:
                return html
            else:
                retry_count -= 1
        except Exception as e:
            print(e)
            retry_count -= 1
    html = requests.get(url, headers=headers, timeout=(5, 10))
    time.sleep(1)
    # 出错5次, 删除代理池中代理
    delete_proxy(proxy)
    if html.status_code == 200:
        return html
    else:
        return



# 解析页面
def parse_page(content):
    items = re.findall('<div class="item">.*?>(\d+)</em>.*?href="(.*?)".*?src="(.*?)".*?div class="hd">(.*?)</div>.*?class="bd">.*?</p>.*?class="star.*?rating_num.*?>(.*?)</span>.*?<span>(\d+)人评价.*?</div>(.*?)</div>.*?</li>', content, re.S)
    for i in range(len(items)):
        items[i] = list(items[i])
        items[i][0] = int(items[i][0])
        items[i][3] = re.sub(';|&nbsp;|/&nbsp;', '', re.search('<span.*?>(.*?)</span>', items[i][3]).group(1)).replace('&#39','"')
        items[i][4] = float(items[i][4])
        items[i][5] = int(items[i][5])
        items[i][6] = re.search('inq">(.*?)</span>', items[i][6])
        items[i][6] = items[i][6].group(1) if items[i][6] else items[i][6]
        items[i] = tuple(items[i])
    return items


# 抓取电影详细信息
def movie_info(url):
    movie_page = page_source(url).text
    release_year = none_group(re.search('<h1>.*?year">\((\d+)\)</span>', movie_page, re.S))
    info = none_group(re.search('<div id="info">(.*?)</div>', movie_page, re.S))
    directors = none_group(re.search('导演.*?directedBy">(.*?)</a>', info, re.S))
    writers = str(re.findall('<a.*?>(.*?)</a>', none_group(re.search('编剧.*?<span(.*?)</span>', info, re.S))))
    actors = str(re.findall('starring">(.*?)</a>', none_group(re.search('主演.*?<span(.*?)</span>', info, re.S))))
    movie_type = str(re.findall('genre">(.*?)</span>', none_group(re.search('类型.*?(<span.*?<br/>)', info, re.S))))
    producing_countries = none_group(re.search('制片国家.*?</span>(.*?)<br/>', info, re.S))
    language = none_group(re.search('语言.*?</span>(.*?)<br/>', info, re.S))
    release_date = str(re.findall('content="(.*?)"', none_group(re.search('上映日期(.*?)<br/>', info, re.S))))
    length_of_film = none_group(re.search('片长.*?>(\d+分钟)</span><br/>', info, re.S))
    alias = none_group(re.search('又名:</span>(.*?)<br>', info, re.S))
    imdb_link = none_group(re.search('IMDb链接.*?href="(.*?)"', info, re.S))
    item = (alias, release_year, directors, writers, actors, movie_type, producing_countries, language, release_date, length_of_film, imdb_link)
    return item


# 保存至txt文件
def save_to_txt(content):
    with open('C:/Users/abel/Desktop/doubanMovieTop250.txt', 'w', encoding='utf-8') as f:
        f.write(','.join(content.columns.tolist()))
        for i, row in content.iterrows():
            f.write('\n')
            f.write(','.join(content.iloc[i,].astype(str).tolist()))
    return


# 保存至csv文件
def save_to_csv(content):
    with open('C:/Users/abel/Desktop/doubanMovieTop250.csv', 'w', encoding='gb18030', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(content.columns.tolist())
        for i, row in content.iterrows():
            writer.writerow(row)
    return


# 保存至mysql数据库
def save_to_mysql():
    db = pymysql.connect(host=HOST, user=USERNAME, port=PORT, passwd=PASSWD, db=DB, charset='utf8')
    cursor = db.cursor()
    return (db, cursor)


def create_table_sql():
    db, cursor = save_to_mysql()
    sql = f'''
    CREATE TABLE IF NOT EXISTS {TABLE} (
    ranking INT(11) NOT NULL COMMENT '排名',
    link TEXT(200) NOT NULL COMMENT '链接',
    post TEXT(200) NULL COMMENT '海报',
    name TEXT(200) NOT NULL COMMENT '电影名',
    score DECIMAL(2,1) NOT NULL COMMENT '评分',
    eval_num INT(11) NULL DEFAULT 0 COMMENT '评价人数',
    note TEXT NULL COMMENT '精彩短评',
    alias TEXT NULL COMMENT '又名',
    release_year INT(11) NULL COMMENT '发行年份',
    directors VARCHAR(255) NULL COMMENT '导演',
    writers VARCHAR(255) NULL COMMENT '编剧',
    actors TEXT NULL COMMENT '演员',
    movie_type CHAR(50) NULL COMMENT '电影类型',
    producing_countries CHAR(50) NULL COMMENT '发行国家',
    language VARCHAR(255) NULL COMMENT '语言',
    release_date TEXT NULL COMMENT '发行日期',
    length_of_film CHAR(20) NULL COMMENT '电影时长',
    imdb_link VARCHAR(255) NULL COMMENT 'IMDB链接',
    PRIMARY KEY (ranking)
    )ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT '豆瓣电影Top250'
    '''
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
    db.close()
    cursor.close()
    return


# 保存至mongodb数据库
def save_to_mongodb(content):
    pass


# 多进程+代理
def parallel():
    pass


def main(url, row, f):
    row = eval(row)
    movie_item = movie_info(url)
    row = row + list(movie_item)
    # 保存到本地文件
    try:
        f.write('\n' + ','.join([str(x) for x in row]))
    except Exception as e:
        print(e)
    # 保存至数据库
    db, cursor = save_to_mysql()
    sql = f'''
    INSERT INTO {TABLE} VALUES{tuple(row)}
    '''
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        print(e, len(row))
        db.close()
        cursor.close()
    return

    
if __name__ == '__main__':
    start = time.time()
    save_path = 'C:/Users/abel/Desktop/doubanMovieTop250.txt'
    if os.path.exists(save_path):
        os.remove(save_path)
    page_info = []
    columns = ['ranking', 'link', 'post', 'name', 'score', 'eval_num', 'note']
    for index in range(0, 250, 25):
        page = page_source(url_base + str(index))
        items = parse_page(page.text)
        page_info = page_info + items
    infos = pd.DataFrame(page_info, columns=columns)
    # 电影详细信息
    multiprocessing.freeze_support()  # 多进程需要用cmd运行
    p = multiprocessing.Pool(processes=4)
    info_columns = ['release_year', 'directors', 'writers', 'actors', 'movie_type', 'producing_countries', 'language', 'release_date', 'length_of_film', 'imdb_link']
    infos = pd.concat([infos, pd.DataFrame(columns=info_columns)], axis=1)
    # 保存文件
    create_table_sql()
    with open(save_path, 'a+', encoding='utf-8') as f:
        f.write(','.join(columns + info_columns))
        for i, url in enumerate(infos['link']):
            row = infos.loc[i, columns].tolist()
            print(i, url)
            main(url, str(row), f)
#            break
#            p.apply_async(main, args=(url, str(row), f))
    p.close()
    p.join()
#    save_to_txt(infos)  # 多进程只能每次保存一条记录
#    save_to_csv(infos)
    end = time.time()
    print('Finish.Spends %ds' % (end-start))        
