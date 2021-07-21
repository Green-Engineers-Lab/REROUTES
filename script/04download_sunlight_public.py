"""
国土数値情報
公共系太陽光施設種の施設データのdownload
・市町村役場等及び公的集会施設データ(平成22年度)
・文化施設データ(平成25年度)
・学校データ(平成25年度)
・下水道関連施設データ(平成24年度)
・都市地域土地利用細分メッシュデータ(平成28年度)
・工業用地データ(平成21年度)
・廃棄物処理施設データ(平成24年度)
・河川データ(平成18年度~平成21年度)
・駅別乗降客数データ(平成29年度)
・道路データ(平成7年度)
・土地利用細分メッシュデータ(平成28年度)
・農業地域データ(平成27年度)

"""


# 1.load packages===================================================================================================
from bs4 import BeautifulSoup
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
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
download_path = os.path.join(root_dir, "download\sunlight_public")
os.makedirs(download_path, exist_ok=True)


# 5.関数===========================================================================================
def ChromeDriver(url, path):
    """
    保存先folderの作成とdriverの起動
    input :
        url : driverで開くurl
        path : download先のpath
    output :
        driver : urlを開いたdriverを返す
    """
    # downloadするfolderを作成する
    os.makedirs(path, exist_ok=True)
    # chrome driverを立ち上げる
    #  seleniumを使用する際の保存先の設定
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"download.default_directory" : path,'profile.default_content_setting_values.automatic_downloads': 1}
    chromeOptions.add_experimental_option("prefs",prefs)
    #  chromeを立ち上げる
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
    driver.get(url)
    return driver


def Zipfile(path):
    """
    path先のzipファイル解凍
    input : 
        path : download先のpath
    output :
        none(解凍のみ)    
    """
    # zipファイルpathの取得
    zip_path = os.path.join(path, "*.zip")
    zip_files = glob.glob(zip_path)
    # zipファイルの解凍
    for zip_file in zip_files:
        # zipファイルの解凍先folderを作成
        new_dir=zip_file.rstrip(".zip")
        os.mkdir(new_dir)
        with  zipfile.ZipFile(zip_file) as zip_f:
            zip_f.extractall(new_dir)


def download(url, year, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td),5):
        # 必要な要素だけをまとめる
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # 世界測地系かつdownloadしたい年度の要素だけを抽出する
        if element[0] == "世界測地系" and element[1] == year:
            download_element.append(element)
    # download
    for i in range(len(download_element)):
        # 施設ID,都道府県ID?を取得
        facility_id = download_element[i][3].split("_")
        pref_id = facility_id[0].split("-")
        # pref_idの長さによって必要なIDが変わる
        if len(pref_id) == 2:
            pref_id = pref_id[0]
        elif len(pref_id) == 3:
            pref_id = pref_id[0] + "-" + pref_id[1]
        elif len(pref_id) == 4:
            pref_id = pref_id[0] + "-" + pref_id[1] + "-" + pref_id[2]
        # seleniumでdownload    
        comment = f"javascript:DownLd('{download_element[i][2]}','{download_element[i][3]}','/ksj/gml/data/{pref_id}/{facility_id[0]}/{download_element[i][3]}' ,this);"
        driver.execute_script(comment)
        Alert(driver).accept()
        time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadGym(url,year,folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td),5):
        # 必要な要素だけをまとめる
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # 世界測地系かつdownloadしたい年度の要素だけを抽出する
        if element[0] == "世界測地系" and element[1] == year:
            download_element.append(element)
    # download(先頭の全国データのみ)
    download_element = download_element[0]
    # seleniumでdownload    
    comment = f"javascript:DownLd('{download_element[2]}','{download_element[3]}','/ksj/gml/data/P27/P27-13/{download_element[3]}' ,this);"
    driver.execute_script(comment)
    Alert(driver).accept()
    time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadSchool(url,year,folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td),5):
        # 必要な要素だけをまとめる
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # 世界測地系かつdownloadしたい年度の要素だけを抽出する
        if element[0] == "世界測地系" and element[1] == year:
            download_element.append(element)
    # download(先頭の全国データのみ)
    download_element = download_element[0]
    # seleniumでdownload    
    comment = f"javascript:DownLd('{download_element[2]}','{download_element[3]}','/ksj/gml/data/P29/P29-13/{download_element[3]}' ,this);"
    driver.execute_script(comment)
    Alert(driver).accept()
    time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadIndustrialPark(url,year, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td), 5):
        # 必要な要素だけをまとめる
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # 世界測地系かつdownloadしたい年度の要素だけを抽出する
        if element[0] == "世界測地系" and element[1] == year:
            download_element.append(element)
    # selemiumでdownload
    for i in range(len(download_element)):
        comment = f"javascript:DownLd('{download_element[i][2]}','{download_element[i][3]}','../data/L05/L05-09/{download_element[i][3]}' ,this);"
        driver.execute_script(comment)
        Alert(driver).accept()
        time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadRiver(url, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td), 5):
        # 必要な要素だけをまとめる
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # downloadしたい世界測地系の要素だけを抽出する
        if element[0] == "世界測地系":
            download_element.append(element)
    # selemiumでdownload
    for i in range(len(download_element)):
        comment = f"javascript:DownLd('{download_element[i][2]}','{download_element[i][3]}','../data/W05/{download_element[i][3][:6]}/{download_element[i][3]}' ,this);"
        driver.execute_script(comment)
        Alert(driver).accept()
        time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadStation(url,year, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td), 6):
        element = [tag_td[i].getText(),tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText(),tag_td[i+4].getText()]
        # 世界測地系かつdownloadしたい年度の要素だけを抽出する
        if element[1] == "世界測地系" and element[2] == year:
            download_element.append(element)
    # selemiumでdownload
    for i in range(len(download_element)):
        comment = f"javascript:DownLd('{download_element[i][3]}','{download_element[i][4]}','../data/S12/S12-18/{download_element[i][4]}' ,this);"
        driver.execute_script(comment)
        Alert(driver).accept()
        time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadRoad(url, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # selemiumでdownload
    comment = "javascript:DownLd('23.96MB', 'N01-07L-48-01.0a_GML.zip',  '../data/N01/N01-07L/N01-07L-48-01.0a_GML.zip' ,this);"
    driver.execute_script(comment)
    Alert(driver).accept()
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


def downloadAgriculture(url, year, folder_name):
    """
    url先の施設データをdownload
    input : 
        url : downloadしたい国土数値情報のurl
        year : downloadしたい年度
        folder_name : download先のfolder名
    output :
        none(downloadと解凍のみ)
    """
    # 保存先のpath
    download_new_path = os.path.join(download_path, folder_name)
    # chrome driverの立ち上げ
    driver = ChromeDriver(url, download_new_path)
    # url先のhtmlを読み込む
    html = urlopen(url)
    # BeautifuSoupで"td"タグ、class=="txtCenter"を取得する
    bsObj = BeautifulSoup(html,'html.parser')
    tag_td = bsObj.find_all("td",class_="txtCenter")    
    # tag_tdの中からdownloadする要素だけを抽出する
    download_element = []
    for i in range(0, len(tag_td), 5):
        element = [tag_td[i+1].getText(),tag_td[i+2].getText(),tag_td[i+3].getText()]
        # downloadしたい年度の要素だけを抽出する
        if element[0] == year:
            download_element.append(element)
    # selemiumでdownload
    for i in range(len(download_element)):
        comment = f"javascript:DownLd('{download_element[i][1]}','{download_element[i][2]}','../data/A12/A12-15/{download_element[i][2]}' ,this);"
        driver.execute_script(comment)
        Alert(driver).accept()
        time.sleep(3)
    # 5秒待ってからdriverを閉じる
    time.sleep(5)
    driver.quit()
    # zipファイルの解凍
    Zipfile(download_new_path)


# 6.施設データdownload=================================================================================
# 市町村役場等及び公的集会施設データ(平成22年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P05.html"
download(url, "平成22年", "publicholl")
# 文化施設データ(平成25年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P27.html"
test = downloadGym(url, "平成25年", "gym")
# 学校データ(平成25年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P29.html"
test = downloadSchool(url, "平成25年", "school")
# 下水道関連施設データ(平成24年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P22.html"
download(url, "平成24年", "sewerage")
# 都市地域土地利用細分メッシュデータ(平成28年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L03-b-u.html"
download(url, "平成28年", "factory")
# 工業用地データ(平成21年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L05.html"
downloadIndustrialPark(url, "平成21年", "industrialpark")
# 廃棄物処理施設データ(平成24年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P15.html"
download(url, "平成24年", "final_disposal")
# 河川データ(平成18年度~平成21年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-W05.html"
downloadRiver(url, "riverbank")
# 駅別乗降客数データ(平成29年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v2_3.html"
downloadStation(url, "平成29年", "station")
# 道路データ(平成7年度)
url = "https://nlftp.mlit.go.jp/ksj/gmlold/datalist/gmlold_KsjTmplt-N01.html"
downloadRoad(url, "road")
# 土地利用細分メッシュデータ(平成28年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L03-b.html"
download(url,"平成28年", "landuse")
# 農業地域データ(平成27年度)
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A12.html"
downloadAgriculture(url,"平成27年", "agriculture")