from bs4 import BeautifulSoup
import requests
import json
from selenium import webdriver  # 有些动态网页抓包困难、或URL含大量加密参数（如天猫评价）
import time


"""
json.load()从文件中读取json字符串
json.loads()将json字符串转换为字典类型
json.dumps()将python中的字典类型转换为字符串类型
json.dump()将json格式字符串写到文件中
"""

# 通过抓包获取京东评价真实地址
url = 'https://item.jd.com/100012043978.html#comment'
url_comment = 'https://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98&productId=100012043978&score=0&sortType=5&page=1&pageSize=10&isShadowSku=0&rid=0&fold=1'
res = requests.get(url_comment).text
json_string = res[res.find('{'):-2]
json_data = json.loads(json_string)
comment_list = json_data['comments']
for comment in comment_list:
    print(comment['id'], comment['content'])
    
    
# selenium抓取天猫评论，网址待用中文解析
url_tmall = 'https://chaoshi.detail.tmall.com/item.htm?spm=a220m.1000858.0.0.4dd96ef9qEbH8b&id=599140369972&is_b=1&cat_id=2&q=%25C3%25A9%25CC%25A8%25BE%25C6%20%25B7%25C9%25CC%25EC%2053%20%25B6%25C8'
driver = webdriver.Chrome()
driver.implicitly_wait(20)  # 隐形等待，最长20秒
driver.get(url_tmall)
time.sleep(5)

for i in range(3):
    # 下滑到页面底部
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # 转换iframe,再找到查看更多，点击
    driver.switch_to.frame(driver.find_element_by_css_selector('iframe[title="livere"]'))
    load_more = driver.find_element_by_css_selector('button.more-btn')
    load_more.click()
    # 把iframe再转回去
    driver.switch_to.default_content()
    time.sleep(2)
    driver.swtich_to.frame(driver.find_element_by_css_selector('iframe e[title="livere"]'))
    comments = driver.find_elements_by_css_selector('div.reply-content')
    for eachcomment in comments:
        content = eachcomment.find_element_by_tag_name('p')
        print(content.text)
# 网页源代码
with open('C:/Users/abel/Desktop/tmall.txt', 'w', encoding='gb18030') as f:
    f.write(driver.page_source)
# 获取评论
comment = driver.find_element_by_css_selector('div.tm-rate-content')
comment = comment.find_element_by_css_selector('div.tm-rate-fulltxt')
print(comment.text)

































