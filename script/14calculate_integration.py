"""
csvファイルの統合
GISデータへの移行

"""

# 1.load packages=============================================================
import arcpy
import os
import pandas as pd
import glob
import gc
from decimal import Decimal, ROUND_HALF_UP
# for logging
import json
from logging import getLogger, config
logger = getLogger(__name__)


# 2.root_dirの設定==============================================================
root_dir = r"C:\Users\GE\Documents\REROUTES-main"


# Logの設定 ===================================================================
with open(os.path.join(root_dir, 'script/log_config.json'), 'r') as f:
    log_conf = json.load(f)
logfname = os.path.join(root_dir, "log", f"log_14_calculate_mesh.log")
if not os.path.isdir(os.path.join(root_dir, "log")):
    os.makedirs(os.path.join(root_dir, "log"))
if os.path.isfile(logfname):
    os.remove(logfname)
log_conf["handlers"]["fileHandler"]["filename"] = logfname
config.dictConfig(log_conf)
logger.info('Start 14calculate_integration.py program...')


# 3.pathの設定==============================================================
logger.info('3. path setting...')
# 再エネマップの最終的な保存先
output_path = os.path.join(root_dir, "remap")
os.makedirs(output_path, exist_ok=True)
# 再エネポテンシャルを統合したcsvの保存先
outcsv_path = os.path.join(root_dir, r"result\potential_integrated_csv")
os.makedirs(outcsv_path, exist_ok=True)


# 4.ファイル名設定===========================================================
logger.info('4. file name setting...')
# 作成したメッシュデータ
mesh = os.path.join(root_dir, r"result\mesh\mesh500m_land_city.shp")
# 作成したreposのcsvデータ
repos = os.path.join(root_dir, r"result\repos_csv\*.csv")
# 作成したsunlight_publicのcsvデータのpath
sunlight_public = os.path.join(root_dir, r"result\sunlight_public_csv\*.csv")
"""
====field名一覧====
=REPOS=
・onshore
・offshore
・building
・geoflash
・river
=sunlight_public=
公共系建築物
・publichall
・gym
・school
・univ
・sewerage
工場・発電所・物流施設
・factory
・induspark
低・未利用地
・gene_final
・indu_final
・riverbank 
・JR
・PR
・road
・coast
・golf
農地
・ricefield
・abandoned
"""

def decimal(string):
    """
    四捨五入により整数値を返す
    input :
        string : 文字列
    output : 
        integer : 整数値
    """
    integer = Decimal(string).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return integer
""""""


# 5.処理====================================================================
try:
    logger.info('5. Processing integration task...')
    # repos_csvの処理
    logger.info('5.1 repos_csv...')
    repos_files = glob.glob(repos)
    #  pandasで読み込み，結合していく
    #  dataframeに変換し、結合する
    for repos_file in repos_files:
        # dataframeに読み込む
        df_repos = pd.read_csv(repos_file, encoding = "utf-8", dtype={'KEY_CODE': object})
        if repos_files.index(repos_file) == 0:
            df_merged_repos = df_repos
        else:
            df_merged_repos = pd.merge(df_merged_repos, df_repos, on='KEY_CODE', how='outer')
        gc.collect()
except Exception as e:
    logger.error("Error!!! See 5.1, please!")
    logger.error(e)


# sunlight_public_csvの処理
logger.info('5.2 sunlight_public_csv...')
try:
    sunlightpublic_files = glob.glob(sunlight_public)
    #  pandasで読み込み，結合していく
    #  dataframeに変換し、結合する
    for sunlightpublic_file in sunlightpublic_files:
        # dataframeに読み込む
        df_sunlightpublic = pd.read_csv(sunlightpublic_file, encoding = "utf-8", dtype={'KEY_CODE': object})
        if sunlightpublic_files.index(sunlightpublic_file) == 0:
            df_merged_public = df_sunlightpublic
        else:
            df_merged_public = pd.merge(df_merged_public, df_sunlightpublic, on='KEY_CODE', how='outer')
        gc.collect()
    #  公共系太陽光はカテゴリごとに分類する
    df_merged_public = df_merged_public.fillna(0)
    df_merged_public["publicSun"] = df_merged_public["publichall"] + df_merged_public["gym"] + df_merged_public["school"] + df_merged_public["univ"] + df_merged_public["sewerage"]
    df_merged_public["factorySun"] = df_merged_public["factory"] + df_merged_public["induspark"]
    df_merged_public["unusedSun"] = df_merged_public["gene_final"] + df_merged_public["indu_final"] + df_merged_public["riverbank"] + df_merged_public["JR"] + df_merged_public["PR"] + df_merged_public["road"] + df_merged_public["coast"] + df_merged_public["golf"]
    df_merged_public["farmSun"] = df_merged_public["ricefield"] + df_merged_public["abandoned"]
    #  上記4fieldだけを抽出
    df_merged_public = df_merged_public[["KEY_CODE", "publicSun", "factorySun", "unusedSun", "farmSun"]]
except Exception as e:
    logger.error("Error!!! See 5.2, please!")
    logger.error(e)


# reposとsunlight_publicを結合
try:
    logger.info('5.3 merging repos and sunlight_public...')
    df_merged = pd.merge(df_merged_repos, df_merged_public, on='KEY_CODE', how='outer')
    # unnamed列を消去
    colnames = df_merged.columns.to_list()
    dropcol = [col for col in colnames if "Unnamed" in col]
    df_merged = df_merged.drop(columns=dropcol)
    df_merged = df_merged.fillna(0)
    # 整数値として保存(小数点第一位で四捨五入)
    colnames = df_merged.columns.to_list()
    for col in colnames[1:]:
        df_merged[col] = df_merged[col].apply(decimal)
    # 再エネ総量の列を作成
    df_merged["RE"] = df_merged["onshore"] + df_merged["offshore"] + df_merged["building"] + df_merged["river"] + df_merged["geoflash"] + df_merged["publicSun"] + df_merged["factorySun"] + df_merged["unusedSun"] + df_merged["farmSun"]
    # csvとして保存
    potential_csv = os.path.join(outcsv_path, "potential_integrated.csv")
    df_merged.to_csv(potential_csv)
    # meshのKEY_CODEをLONGで準備する(joinのために)
    # add field
    arcpy.AddField_management(mesh, "KEYCODEint", "LONG")
    # calculate field
    arcpy.CalculateField_management(mesh, "KEYCODEint", "int(!KEY_CODE!)","PYTHON3")
    # meshと結合する
    #  field名のテーブル名による修飾を無効化
    arcpy.env.qualifiedFieldNames = False
    remap = os.path.join(output_path, "remap.shp")
    joined_table = arcpy.AddJoin_management(mesh, "KEYCODEint", potential_csv , "KEY_CODE")
    arcpy.CopyFeatures_management(joined_table, remap)
except Exception as e:
    logger.error("Error!!! See 5.3, please!")
    logger.error(e)

logger.info("Finished 14 calculate_integration.py")
