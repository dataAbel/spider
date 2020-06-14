import requests
from bs4 import BeautifulSoup
import re
import csv
import time


# 第N页的网页源代码
def page_source(page):
    try:
        res = requests.get(url % page, headers=headers)
    except Exception as e:
        print(e)
    return res


# 解析网页
def house_detail(response):
    soup = BeautifulSoup(response.text, 'lxml')
    houses = soup.find_all('li', class_='list-item')
    for house in houses:
        name = re.sub('\s{2,}', ' ', house.find('div', class_='house-title').a.string).strip().replace('"', '')
        items1 = house.find('div', class_='details-item').text.split('|')
        rooms, area, floor, built_year = [i.strip() for i in items1 + ['Null'] * (4 - len(items1))]
        built_year = built_year.strip()
        items2 = [re.sub('\s', '', i) for i in house.find('span', class_='comm-address').text.split('\xa0\xa0')]
        community, address = items2 + ['Null'] * (2 - len(items2))
        broker = house.find('span', class_=['broker-name', 'broker-text']).text
        price = house.find('span', class_='price-det').text
        avg_price = house.find('span', class_='unit-price').text.split('元')[0]
        yield [name, rooms, area, floor, built_year, community, address, price, avg_price, broker]


def save_to_mysql():
    pass


if __name__ == '__main__':
    start = time.time()
    url = 'https://shanghai.anjuke.com/sale/p%d/#filtersort'
    # 添加请求头，不然会被封IP
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    with open('C:/Users/abel/Desktop/anjuke.csv', 'a+', newline='', encoding='gb18030') as f:
#    with open('/home/code/anjuke.csv', 'a+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'rooms', 'area', 'floor', 'built_year', 'community', 'address', 'price', 'avg_price', 'broker'])
        for page in range(1, 51):
            print('正在抓取第%d页：' % page)
            time.sleep(5)  # 限制爬取速度，否则需要验证
            response = page_source(page)
            for item in house_detail(response):
                writer.writerow(list(item))
    print('Finishi:spends %d s.' % (time.time() - start))
        