"""
標準地域メッシュ
2分の1地域メッシュデータのdownload

"""


# 1.load packages===================================================================================================
from selenium import webdriver
import time
import glob
import zipfile
import os


# 2.root_dirの設定====================================================================================================
root_dir = r"C:\Users\GE\Documents\REROUTES-main"


# 3.pathの設定=========================================================================================================
# chrome driverのpath
chromedriver = os.path.join(root_dir, r"chromedriver_win32\chromedriver.exe")
# download先のpath
download_path = os.path.join(root_dir, "download\mesh")
os.makedirs(download_path, exist_ok=True)


# 4.Chrome Driverを立ち上げる=========================================================================================
# seleniumを使用する際の保存先の設定
chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory" : download_path,'profile.default_content_setting_values.automatic_downloads': 1}
chromeOptions.add_experimental_option("prefs",prefs)
# chromeを立ち上げる
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)


# 5.標準地域メッシュ(2分の1地域メッシュ)のdownload========================================================================================================
# 1ページから9ページまで
for page in range(1,10):
    # eStatの世界測地系緯度経度4次メッシュ(2分の1地域メッシュ)を開く
    url = f"https://www.e-stat.go.jp/gis/statmap-search?page={page}&type=2&aggregateUnitForBoundary=H&coordsys=1&format=shape"
    driver.get(url)
    time.sleep(3)
    # ページ内のリンク20個をdownload
    try:
        for i in range(1, 21):
            # ページ内のリンク20個のうちi番目をdownload
            xpath = f"/html/body/div[1]/div/main/div[2]/section/div[2]/main/section/div[4]/div/div/article[{i}]/div/ul/li[3]/a"
            link = driver.find_element_by_xpath(xpath).get_attribute("href")
            driver.get(link)
            time.sleep(3)
    except Exception as e:
        # page9はリンクが20個ないのでスルー
        print("download完了")
    # pageの遷移は1秒待つ
    time.sleep(1)
# 5秒待ってからdriverを閉じる
time.sleep(5)
driver.quit()


# 6.全てのzipファイルを解凍============================================================================================================================
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

