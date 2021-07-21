"""
REPOS
再生可能エネルギー情報提供システムからdownload
・住宅系太陽光発電
・陸上風力発電
・洋上風力発電
・地熱発電（蒸気フラッシュ）
・中小水力発電

"""


# 1.load packages===================================================================================================
from bs4 import BeautifulSoup
from urllib.request import urlopen
from selenium import webdriver
import time
import glob
import zipfile
import os

# 2.root_dirの設定====================================================================================================
root_dir = r"C:\Users\GE\Desktop\remap_test"


# 3.pathの設定=========================================================================================================
# chrome driverのpath
chromedriver = r"C:\Program Files\chromedriver_win32\chromedriver.exe"
# download先のpath
download_path = os.path.join(root_dir, r"download\repos")
os.makedirs(download_path, exist_ok=True)


# 4.Chrome Driverを立ち上げる=========================================================================================
# seleniumを使用する際の保存先の設定
chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory" : download_path,'profile.default_content_setting_values.automatic_downloads': 1}
chromeOptions.add_experimental_option("prefs",prefs)
# chromeを立ち上げる
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)


# 5.REPOSからdownload=======================================================================================================
# REPOSのhtmlを読み込む
url = "http://www.renewable-energy-potential.env.go.jp/RenewableEnergy/21.html"
html = urlopen(url)
# BeautifulSoupで"a"タグを取得する
bsObj = BeautifulSoup(html,'html.parser')
tag_a = bsObj.find_all("a")
# "a"タグの中からhrefのみを取得
hrefs = []
for i in range(len(tag_a)):
    hrefs.append(tag_a[i].get("href"))
# hrefの中から今回対象となるエネルギー種のリンクのみを抽出
download_url = []
energies = ["sunlight_building_i_s",
          "wind_land_i_s",
          "wind_sea_i_s",
          "water_river_i_s",
          "geo_steam150_i_s"]
for href in hrefs:
    for energy in energies: 
        # hrefの中にenergyの文字列があれば抽出
        if energy in href:
            # 熱利用は省く
            if "thermal" not in href:
                # downloadするurlリストを作成
                download_url.append(url.rstrip("21.html") + href)
                break
# urlのリストから1つずつdownloadする
for url in download_url:
    driver.get(url)
    time.sleep(3)
# 5秒待ってからdriverを閉じる
time.sleep(5)
driver.quit()


# 6.全てのzipファイルを解凍======================================================================================================
# zipファイルpathの取得
zip_path = os.path.join(download_path, "*.zip")
zip_files = glob.glob(zip_path)
# zipファイルの解凍
for zip_file in zip_files:
    # zipファイルの解凍先folderを作成
    new_dir = zip_file.rstrip(".zip")
    os.mkdir(new_dir)
    with  zipfile.ZipFile(zip_file) as zip_f:
        zip_f.extractall(new_dir)
