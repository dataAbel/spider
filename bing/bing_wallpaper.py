import requests
from bs4 import BeautifulSoup
from lxml import etree
import datetime
import time
import re
import os
import win32api,win32con,win32gui


today = datetime.date.today()
url_base = 'https://bing.ioliu.cn'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'}
save_path = 'C:/Users/abel/Desktop/wallpaper'


# 获取网页源代码
def page_source(url):
    response = requests.get(url, headers=headers)
    return response


# 解析网页源代码
def load_img():
    res = page_source(url_base)
    soup = BeautifulSoup(res.text, 'html.parser')
    url_img = soup.select('.mark')[0]['href']
    url = 'http://h1.ioliu.cn/bing' + re.search("/photo(.*?)\?", url_img).group(1) + '_1920x1080.jpg'
    img_content = page_source(url)
    return soup, img_content


# 更换壁纸
def set_wall_paper(pic_path):
    key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER,"Control Panel\\Desktop",0,win32con.KEY_SET_VALUE)
    win32api.RegSetValueEx(key, "WallpaperStyle", 0, win32con.REG_SZ, "2") 
    win32api.RegSetValueEx(key, "TileWallpaper", 0, win32con.REG_SZ, "0")
    win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, pic_path, win32con.SPIF_SENDWININICHANGE)


if __name__ == '__main__':
    # 保存到桌面
    soup, content = load_img()
    fname = '{0}/{1}.jpg'.format(save_path, str(today) + '_' + soup.h3.string.split(' ')[0])
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    with open(fname, 'wb+') as f:
        f.write(content.content)
    set_wall_paper(fname)
