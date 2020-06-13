import requests
import time
import execjs
import pymysql
from retrying import retry
import multiprocessing


# 基础信息
BASE_URL = 'http://fund.eastmoney.com/pingzhongdata/'
FUND_LIST_URL = 'http://fund.eastmoney.com/js/fundcode_search.js'
headers = {
    'Host': 'fund.eastmoney.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
    }


# 服务器信息
HOST = 'localhost'
PORT = 3306
USER = 'home'
PASSWORD = input('Please input your password:')
DB = 'abel'
TABLE = 'fund'


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


@retry(stop_max_attempt_number=5)
def get_html(url):
    retry_count = 5
    proxy = get_proxy().get("proxy")
    while retry_count > 0:
        try:
            html = requests.get(url, proxies={"http": "http://{}".format(proxy)}, headers=headers, timeout=(5, 10))
            # 使用代理访问
            if html.status_code == 200:
                return html
            else:
                retry_count -= 1
        except Exception:
            retry_count -= 1
    html = requests.get(url, headers=headers, timeout=(5, 10))
    # 出错5次, 删除代理池中代理
    delete_proxy(proxy)
    if html.status_code == 200:
        return html  
#    return None


# 接口构造

# 构造基金url
def fund_url(fund_code):
    now = time.strftime('%Y%m%d%H%M%S', time.localtime())
    url = f'{BASE_URL}{fund_code}.js?v={now}'
    return url


# 从js文件中提取字段值
def extract_js(script, col):
    try:
        value = script.eval(col)
    except:
        value = 'NULL'
    return value


# 获取指定基金各指标数据
def fund_index(fund_code):
    try:
        content = get_html(fund_url(fund_code))
    except Exception as e:
        print(fund_code, e)
        return None
    if (not content) or (content.status_code != 200):
        print(fund_code, content.status_code)
        return None
    js_content = execjs.compile(content.text)
    
    name = extract_js(js_content, 'fS_name')  # 基金名称
    code = extract_js(js_content, 'fS_code')  # 基金代码
    source_rate = extract_js(js_content, 'fund_sourceRate')  # 原费率
    source_rate = float(source_rate) if source_rate not in ['NULL', ''] else source_rate
    rate = extract_js(js_content, 'fund_Rate')  # 现费率
    rate = float(rate) if rate not in ['NULL', ''] else rate
    minsg = extract_js(js_content, 'fund_minsg')  # 最小申购金额
    minsg = int(minsg) if minsg not in ['NULL', ''] else minsg
    stock_codes = str(extract_js(js_content, 'stockCodes'))  # 基金持仓股票代码
    bond_codes = str(extract_js(js_content, 'zqCodes'))  # 基金持仓债券代码
    stock_codes_new = str(extract_js(js_content, 'stockCodesNew'))  # 基金持仓股票代码(新市场号)
    bond_codes_new = str(extract_js(js_content, 'zqCodesNew'))  # 基金持仓债券代码(新市场号)
    profitability_1y = extract_js(js_content, 'syl_1n')  # 近1年收益率
    profitability_1y = float(profitability_1y) if profitability_1y not in ['NULL', ''] else profitability_1y
    profitability_6m = extract_js(js_content, 'syl_6y')  # 近6个月收益率
    profitability_6m = float(profitability_6m) if profitability_6m not in ['NULL', ''] else profitability_6m
    profitability_3m = extract_js(js_content, 'syl_3y')  # 近3个月收益率
    profitability_3m = float(profitability_3m) if profitability_3m not in ['NULL', ''] else profitability_3m
    profitability_1m = extract_js(js_content, 'syl_1y')  # 近1个月收益率
    profitability_1m = float(profitability_1m) if profitability_1m not in ['NULL', ''] else profitability_1m
    stock_position = str(extract_js(js_content, 'Data_fundSharesPositions'))  # 股票仓位测算图
    net_worth_trend = str(extract_js(js_content, 'Data_netWorthTrend'))  # 单位净值走势：x-毫秒时间戳，y-单位净值，equityRetury-净值回报，unitMoney-每份派送金
    ac_worth_trend = str(extract_js(js_content, 'Data_ACWorthTrend'))  # 累计净值走势
    profitability_cum = str(extract_js(js_content, 'Data_grandTotal'))  # 累计收益率净值走势
    similar_ranking = str(extract_js(js_content, 'Data_rateInSimilarType'))  # 同类排名走势
    similar_ranking_pcnt = str(extract_js(js_content, 'Data_rateInSimilarPersent'))  # 同类排名百分比
    fluctuation_scale = str(extract_js(js_content, 'Data_fluctuationScale'))  # 规模变动：mom-较上期变动环比
    holder_structure= str(extract_js(js_content, 'Data_holderStructure'))  # 持有人结构
    asset_conf= str(extract_js(js_content, 'Data_assetAllocation'))  # 资产配置
    performance_evaluation= str(extract_js(js_content, 'Data_performanceEvaluation'))  # 业绩评价：['选股能力', '收益率', '抗风险', '稳定性','择时能力']
    current_manager = str(extract_js(js_content, 'Data_currentFundManager'))  # 现任基金经理
    buy_sedemption = str(extract_js(js_content, 'Data_buySedemption'))  # 申购赎回
    swith_same_type = str(extract_js(js_content, 'swithSameType'))  # 同类基金涨幅榜
    
    result = [name, code, source_rate, rate, minsg, stock_codes, bond_codes,
              stock_codes_new, bond_codes_new, profitability_1y, profitability_6m,
              profitability_3m, profitability_1m, stock_position, net_worth_trend,
              ac_worth_trend, profitability_cum, similar_ranking, similar_ranking_pcnt,
              fluctuation_scale, holder_structure, asset_conf, performance_evaluation,
              current_manager, buy_sedemption, swith_same_type]
    result = [i.replace("'", '"') if isinstance(i, str) and i else i for i in result]
    result = [i if i else "NULL" for i in result]
    return result
    

# 13位毫秒时间戳转换为日期时间戳。如果10位的话是秒时间戳
def timestamp_to_datetime(millisecond_timestamp):
    timestamp = float(millisecond_timestamp/1000)  # 转换为秒
    time_array = time.localtime(timestamp)
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return datetime


# 获取所有基金数据
def fund_list():
    content = requests.get(FUND_LIST_URL)
    js_content = execjs.compile(content.text)
    raw_data = js_content.eval('r')
    all_code = [x[0] for x in raw_data]
    return all_code


# 连接数据库
def conn_mysql():
    db = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, db=DB, charset='utf8')
    cursor = db.cursor()
    return (db, cursor)


# mysql插入单条记录
def insert_record_to_mysql(db, cursor, record):
    place_holders = ','.join(["'%s'", "'%s'", '%s', '%s', '%s', "'%s'", "'%s'", "'%s'", "'%s'",
                              '%s', '%s', '%s', '%s'] + ["'%s'"] * 13)
    sql = f'''INSERT INTO {TABLE} VALUES ({place_holders})''' % tuple(record)  # ','.join(["'%s'"] * 26)
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        print('Insert Error:', e)
        db.rollback()
    return


def main(fund):
    db, cursor = conn_mysql()
    print('正在抓取：%s' % fund)
    record = fund_index(fund)
    # 保存到数据库
    if record and record[0] != 'NULL':
        insert_record_to_mysql(db, cursor, record)
    cursor.close()
    db.close()
    return


if __name__ == '__main__':
    start = time.time()
    # 连接数据库
#    db, cursor = conn_mysql()
    # 查询基金列表
    funds = fund_list()
    multiprocessing.freeze_support()  # 多进程需要用cmd运行
    p = multiprocessing.Pool(processes=6)
    # 遍历每个基金的各指标信息
    for fund in funds:
        p.apply_async(main, args=(fund,))
#        print('正在抓取：%s' % fund)
#        record = fund_index(fund)
#        # 保存到数据库
#        if record:
#            insert_record_to_mysql(cursor, record)
    p.close()
    p.join()

    # 关闭数据库
#    db.close()
    print('Finish!Spends %ds' % (time.time() - start))
