"""
日本
平成31年度行政区域データのdownload

"""


# 1.load packages===================================================================================================
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
download_path = os.path.join(root_dir, "download\japan")
os.makedirs(download_path, exist_ok=True)


# 4.Chrome Driverを立ち上げる=========================================================================================
# seleniumを使用する際の保存先の設定
chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory" : download_path,'profile.default_content_setting_values.automatic_downloads': 1}
chromeOptions.add_experimental_option("prefs",prefs)
# chromeを立ち上げる
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)


# 3.行政区域のdownload==============================================================================================
# 国土数値情報　行政区域データページを開く
url = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-v2_3.html"
driver.get(url)
# seleniumでdownload
comment = "javascript:DownLd('396.68MB','N03-190101_GML.zip','../data/N03/N03-2019/N03-190101_GML.zip' ,this);"
driver.execute_script(comment)
Alert(driver).accept()
time.sleep(20)
driver.quit()


#4.zipファイルを解凍======================================================================================================
#zipファイルpathの取得
zip_path = os.path.join(download_path, "*.zip")
zip_file = glob.glob(zip_path)
#zipファイルの解凍
# zipファイルの解凍先folderを作成
new_dir = zip_file[0].rstrip(".zip")
os.mkdir(new_dir)
# 解凍
with  zipfile.ZipFile(zip_file[0]) as zip_f:
    zip_f.extractall(new_dir)
