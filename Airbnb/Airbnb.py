# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 01:26:15 2020
@author: abel
@email: dataAbel@outlook.com
"""

from selenium import webdriver
import time
import re


def rent_info(page):
    driver.get(url_base % page)
    time.sleep(5)
    elements = driver.find_elements_by_css_selector('div._gig1e7')
    for i, element in enumerate(elements):
        name = element.find_element_by_css_selector('div._qrfr9x5').text
        details = element.find_element_by_css_selector('span._faldii7').text.split(' · ')
        try:
            house_type = details[0]  # 房屋类型、大小
            bed_number = details[1]
        except:
            bed_number = 'Null'
        try:
            comment_num = int(element.find_element_by_css_selector('span._69pvqtq').text)
        except:
            comment_num = 0
        price = int(re.search('(\d+)', element.find_element_by_css_selector('span._1d8yint7').text, re.S).group(1))
        try:
            discount = element.find_element_by_css_selector('span._6vwvwy7').text()
        except:
            discount = 'Null'
        link = element.find_element_by_css_selector('a._surdeb').get_attribute('href')
        yield [name, house_type, bed_number, comment_num, price, discount, link]

        
if __name__ == '__main__':
    url_base = 'https://www.airbnb.cn/s/上海/homes?section_offset=4&items_offset=%d&map_toggle=false'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
    url = 'https://www.airbnb.cn/s/%E4%B8%8A%E6%B5%B7/homes?refinement_paths%5B%5D=%2Fhomes&current_tab_id=home_tab&selected_tab_id=home_tab&section_offset=4&items_offset=20&map_toggle=false&screen_size=large&hide_dates_and_guests_filters=false&s_tag=cua7zZ1f&place_id=ChIJMzz1sUBwsjURoWTDI5QSlQI&last_search_session_id=8dd6814a-b7bd-45d0-9fd5-7c6953edc32a'
    
    # 打开浏览器
    driver = webdriver.Chrome()
    
    # 获取总页数
    driver.get(url_base % 0)
    driver.implicitly_wait(5)
    total_pages = int(driver.find_elements_by_css_selector('a._13n1po3b')[-1].text)
    
    # 抓取短租信息
    with open('C:/Users/abel/Desktop/苦行僧/爬虫/data/Airbnb.txt', 'w', encoding='utf-8') as f:
        f.write('name\thouse_type\tbed_number\tcomment_num\tprice\tdiscount\tlink')
        for page in range(total_pages):
            print('正在抓取第%d页...' % (page + 1))
            for info in rent_info(page * 20):
                f.write('\n' + '\t'.join([str(x) for x in info]))
    print('Finish')
        
