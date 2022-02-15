"""
公共系太陽光ポテンシャルの高空間解像度化

"""

# 1.load packages=============================================================
import arcpy
import os
import pandas as pd
import glob
from tqdm import tqdm
# for logging
import json
from logging import getLogger, config
logger = getLogger(__name__)

# 2.root_dirの設定==============================================================
root_dir = r"C:\Users\GE\Documents\REROUTES-main"
# 事前準備が必要な河川別の河川延長と人口化率のデータのpathをここに
riverbank_prepared_csv = os.path.join(root_dir, r"data\riverbank_prepared\river_bank_data_modify.csv")

# Logの設定 ===================================================================
with open(os.path.join(root_dir, 'script/log_config.json'), 'r') as f:
    log_conf = json.load(f)
logfname = os.path.join(root_dir, "log", f"log_13_calculate_sunlight_public.log")
if not os.path.isdir(os.path.join(root_dir, "log")):
    os.makedirs(os.path.join(root_dir, "log"))
if os.path.isfile(logfname):
    os.remove(logfname)
log_conf["handlers"]["fileHandler"]["filename"] = logfname
config.dictConfig(log_conf)
logger.info('Start 13calculate_sunlight_public_test.py program...')

# 3.pathの設定==============================================================
logger.info('3. Path setting...')
# download先のpathに合わせる
download_path = os.path.join(root_dir, "download\sunlight_public")
# 処理途中で生じる生成物の保存先
calculate_path = os.path.join(root_dir, "calculate\sunlight_public")
os.makedirs(calculate_path, exist_ok=True)
# 結果を出力したcsvの保存先
output_path = os.path.join(root_dir, "result\sunlight_public_csv")
os.makedirs(output_path, exist_ok=True)


# 4.ファイル名設定===========================================================
logger.info('4. File name setting...')
#  複数ファイルあるものはpathを記す
# 市町村役場等及び公的集会施設データ(平成22年度)
publichall = os.path.join(download_path, "publichall\**\*.shp")
# 文化施設データ(平成25年度)
gym = os.path.join(download_path,"gym\P27-13\P27-13\P27-13.shp")
# 学校データ(平成25年度)
school = os.path.join(download_path,"school\P29-13\P29-13\P29-13.shp")
# 下水道関連施設データ(平成24年度)
sewerage = os.path.join(download_path, "sewerage\**\*.shp")
# 都市地域土地利用細分メッシュデータ(平成28年度)
factory = os.path.join(download_path, "factory\**\*.shp")
# 工業用地データ(平成21年度)
industrialpark = os.path.join(download_path, "industrialpark\**\*.shp")
# 廃棄物処理施設データ(平成24年度)
disposal = os.path.join(download_path, "final_disposal\**\*.shp")
# 河川データ(平成18年度~平成21年度)
riverbank = os.path.join(download_path, "riverbank\**\*.shp")
# 駅別乗降客数データ(平成29年度)
station = os.path.join(download_path, "station\S12-18_GML\S12-18_NumberOfPassengers.shp")
# 道路データ(平成7年度)
road = os.path.join(download_path, r"road\N01-07L-48-01.0a_GML\N01-07L-2K_Road.shp")
# 土地利用細分メッシュデータ(平成28年度)
landuse = os.path.join(download_path, "landuse\**\*.shp")
# 農業地域データ(平成27年度)
agriculture = os.path.join(download_path, "agriculture")
# 2分の1地域メッシュ
mesh = os.path.join(root_dir, "result\mesh\mesh500m_land_city.shp")
# 日本　行政区域
japan = os.path.join(root_dir, r"download\japan\N03-190101_GML\N03-19_190101.shp")



# 5.関数====================================================================
logger.info('5. Defining functions...')
def Extract(inFeature,expression, outFeature_name):
    '''
    属性選択を行い，選択したものを抽出
    input : 
        inFeature : 入力shape
        expression : 条件式(文字列で入力)
        outFeature_name : 任意に出力shpの命名をしたい場合入力
    output : 
        outFeature : 出力shape
    '''
    # select by attribute & Copy
    if outFeature_name != "":
        inFeature_name = outFeature_name + ".shp"
    else:
        inFeature_name = os.path.basename(inFeature)
    outFeature = os.path.join(calculate_path, inFeature_name.rstrip(".shp") + "_selected.shp")
    feature_selected = arcpy.SelectLayerByAttribute_management(inFeature, "NEW_SELECTION", expression)
    arcpy.CopyFeatures_management(feature_selected, outFeature)
    return outFeature


def GeoExtract(inFeature,selectFeature):
    '''
    空間選択を行い，選択したものを抽出
    input : 
        inFeature : 入力shape
        selectFeature : 選択に使用するshape
    output :
        outFeature : 出力shape
    '''
    # select by location & Copy
    inFeature_name = os.path.basename(inFeature)
    outFeature = os.path.join(calculate_path, inFeature_name.rstrip(".shp") + "_selected.shp")
    feature_selected = arcpy.management.SelectLayerByLocation(inFeature, "INTERSECT",selectFeature)
    arcpy.CopyFeatures_management(feature_selected, outFeature)
    return outFeature


def CalculateField(inFeature,newfield_name,type,expression,codeblock):
    '''
    新しいfieldを追加し，そのfieldに対して演算を実行
    input :
        inFeature : 入力shape
        newfieled_name : 新しいfield名（10文字以下）
        type : 新しいfieldの型
        expression : 条件式(文字列で入力)
        codeblock : pythonコード（文字列で入力）
    output :
        inFeature : 計算後feature
    '''
    # add field
    arcpy.AddField_management(inFeature, newfield_name, type)
    # calculate field
    if codeblock != "":
        arcpy.CalculateField_management(inFeature, newfield_name, expression,"PYTHON3",codeblock)
    else:
        arcpy.CalculateField_management(inFeature, newfield_name, expression,"PYTHON3")
    return inFeature


def GeoCalculateField(inFeature,newfield_name,type,method,unit):
    '''
    新しいfieldを追加し，そのfieldに対して面積[km2]を計算
    input :
        inFeature : 入力shape
        newfiled_name : 新しいfield名（10文字以下）
        type : 新しいfieldの型
        method : 面積，長さの計算方法
        unit : 計算するものの出力単位
    output :
        inFeature : 計算後feature
    '''
    # add field
    arcpy.AddField_management(inFeature, newfield_name, type)
    # calculate Geometry
    if "LENGTH" in method:
        arcpy.CalculateGeometryAttributes_management(inFeature, [[newfield_name, method]],unit,"")
    else:    
        arcpy.CalculateGeometryAttributes_management(inFeature, [[newfield_name, method]],"",unit)
    return inFeature


def IntegrateShapes(inFiles,outName,define):
    '''
    複数shapeの座標定義，merge，座標変換を行う
    input :
        inFiles : 入力shapeのfile名のリスト
        outName : 出力結果の名前を入力
        define : 座標定義をするかしないか
    output :
        outFeature : 出力shape
    '''
    # 計算過程のshapeをcalculate_pathに残していく
    outFeature = os.path.join(calculate_path, f"{outName}.shp")
    # 座標をGCS JCD2011（EPSGコード4612）に変換
    if define == True:
        for inFile in inFiles:
            arcpy.DefineProjection_management(inFile, 4612)
    # merge
    arcpy.Merge_management(inFiles, outFeature)
    # 座標をGCS JCD2011（EPSGコード4612）に変換
    inFeature = outFeature
    outFeature = inFeature.rstrip(".shp") + "_pro.shp"
    arcpy.management.Project(inFeature, outFeature, 6668)
    return outFeature


def IntegrateExactShapes(inFiles,outName,define,expression,processname):
    '''
    複数shapeの座標定義，merge，座標変換を行う
    input :
        inFiles : 入力shapeのfile名のリスト
        outName : 出力結果の名前を入力
        define : 座標定義をするかしないか
    output :
        outFeature : 出力shape
    '''
    # 計算過程のshapeをcalculate_pathに残していく
    outFeature = os.path.join(calculate_path, f"tmp_{processname}", f"{outName}.shp")
    if not os.path.isdir(os.path.join(calculate_path, f"tmp_{processname}")):
        os.makedirs(os.path.join(calculate_path, f"tmp_{processname}"))
    logger.info("Processing feature selection...")
    # import pdb; pdb.set_trace()
    out_selecteds = []
    for inFile in tqdm(inFiles):
        # 座標をGCS JCD2011（EPSGコード4612）に変換
        if define == True:
            arcpy.DefineProjection_management(inFile, 4612)
        # 特定のポリゴンを抽出して上書きする
        out_selected = os.path.join(calculate_path, f"tmp_{processname}", os.path.basename(inFile).rstrip(".shp") + "_selected.shp")
        feature_selected = arcpy.SelectLayerByAttribute_management(inFile, "NEW_SELECTION", expression) # Required == chcp 932, arcgisの文字コードがshift-jis
        arcpy.CopyFeatures_management(feature_selected, out_selected)
        out_selecteds.append(out_selected)
    # merge
    logger.info("Merging shapefiles...")
    arcpy.Merge_management(out_selecteds, outFeature)
    # 座標をGCS JCD2011（EPSGコード4612）に変換
    inFeature = outFeature
    outFeature = inFeature.rstrip(".shp") + "_pro.shp"
    arcpy.management.Project(inFeature, outFeature, 6668)
    return outFeature


def Division(inFeature,all_potential_kwh):
    '''
    featureに対してpotentialを均等に按分する
    input : 
        inFeature : 入力feature
        all_potential_kwh : 日本全国のポテンシャル量[kwh/y]
    output :
        potential_per_facility : 1feature当たりのポテンシャル量[kwh/y]
    '''
    # featureの数をcount
    countFeature = arcpy.GetCount_management(inFeature)
    countFeature = int(countFeature.getOutput(0)) 
    # ポテンシャル量を均等に按分
    potential_per_facility = all_potential_kwh / countFeature
    return potential_per_facility 


def toCSV(inFeature,fieldname,newfieldname):
    '''
    featureのテーブルデータをcsvに出力し，2分の1地域メッシュごとにsummaryして上書き
    input :
        inFeature : 入力shape
        fieledname : 出力したいfield名
        newfieldname : 出力の際にnewfield名に変更したい場合入力
    output :
        outTable : 出力csv
    '''
    # csvに出力
    outTable = os.path.join(calculate_path, f"{fieldname}.csv") 
    arcpy.CopyRows_management(inFeature, outTable)
    # pandasでKEY_CODEごとにsummary
    df = pd.read_csv(outTable,encoding="utf-8",usecols=["KEY_CODE",fieldname])
    #  newfieldnameがあれば、そちらに書き換え
    if newfieldname != "":
        df = pd.rename(columns={fieldname:newfieldname})
        fieldname = newfieldname
    df = df.groupby("KEY_CODE").sum()
    df = df.reset_index()
    df = df[["KEY_CODE",fieldname]]
    # 結果としてcsvに出力
    outTable = os.path.join(output_path, f"{fieldname}_summary.csv") 
    df.to_csv(outTable)
    return outTable


def passenger_ave(d,u,p):
    """
    駅別乗降客数の7年間の平均値を返す
    input:
        d : https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v2_3.html の重複コード
        u : https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v2_3.html データ有無コード
        p : https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v2_3.html の乗降客数
    output:
        data_umu : 7年間で使用できるデータがあったかどうか
        ave : 7年間の平均乗降客数
    """
    # nはデータの個数，sは合計値
    n = 0
    s = 0
    length = len(d)
    for i in range(length):
        # 重複コードで仕分けをする
        if d[i] != 1:
            continue
        else:
            # データ有無
            if u[i] != 1:
                continue
            else:
                # もし新駅ならpが0なので，それは無視
                # 2017が新駅の年だと計算されないことになるが，そもそも客数0で按分されないのでok
                if p[i] != 0:
                    n += 1
                    s += p[i]
                else:
                    continue
    # 平均を計算し，n=0ならばdata_umu = 2とする
    # n>=0ならばdata_umu = 1とする
    if n == 0:
        data_umu = 2
        ave = 0
    else:
        data_umu = 1
        ave = int(s/n)
    return data_umu, ave


# 6.ポテンシャル量推計のためのコードブロックと関数 ================================
logger.info('6. Defining code blocks for arcpy...')
code_publichall = """
def publichall(pref, flag):
    '''
    公民館のポテンシャル推計
    input : 
        pref : 都道府県コード
        flag : 公民館→4, 集会所→5
    output :
        kwh : featureごとのポテンシャル[kwh/y]
    '''
    if pref == " ":
        pref_code = 48
    else:
        pref_code = int(pref[0:2])
    if flag == "4":
        area = kominkan_ave * 0.82
    elif flag == "5":
        area = syukai_ave * 0.82
    else:
        area = 0
    kwh = area * (1/12) * pref_unit[pref_code-1][1]
    return kwh
"""


code_gymChecker = """
def gymChecker(name):
    '''
    学校体育館と重複しているかどうかを判定
    input :
        name : 体育館の名称
    output :
        flag : 学校体育館→0, それ以外の体育館→1
    '''
    if "学校" in name:
        flag = 0
    else:
        flag = 1    
    return flag
"""

code_gym = """
def gym(pref):
    '''
    体育館のポテンシャル推計
    input :
        pref : 都道府県コード
    output :
        kwh : featureごとのポテンシャル量[kwh/y]
    '''
    if pref == " ":
        pref_code = 48
    else:
        pref_code = int(pref[0:2])
    area = gym_ave * 0.54
    kwh = area * (1/12) * pref_unit[pref_code-1][1]
    return kwh
"""


code_school = """
def school(pref, school_id):
    '''
    学校のポテンシャル推計
    input :
        pref : 都道府県コード
        school_id : 学校種識別コード
    output :
        kwh : featureごとのポテンシャル量[kwh/y]
    '''
    if pref == " ":
        pref_code = 48
    else:
        pref_code = int(pref[0:2])
    if school_id == "16001":
        area = ave_16001
    elif school_id == "16002":
        area = ave_16002
    elif school_id == "16003":
        area = ave_16003
    elif school_id == "16004":
        area = ave_16004
    kwh = 0.43 * area * (1/12) * pref_unit[pref_code-1][1]
    return kwh
"""


code_univ = """
def univ(pref,school_id):
    '''
    大学のポテンシャル量推計
    input :
        pref : 都道府県コード
        school_id : 学校種識別コード
    output :
        kwh : featureごとのポテンシャル量
    '''
    if pref == " ":
        pref_code = 48
    else:
        pref_code = int(pref[0:2])
    if school_id == "16005":
        area = ave_16005
    elif school_id == "16007":
        area = ave_16007
    kwh = 0.18 * area * (1/12) * pref_unit[pref_code-1][1]
    return kwh
"""


code_sewerage = """
def sewerage(pref):
    '''
    公共下水のポテンシャル量推計
    input :
        pref : 都道府県コード
    output :
        kwh : featureごとのポテンシャル[kwh/y]
    '''
    if pref == " ":
        pref_code = 48
    else:
        pref_code = int(pref[0:2])    
    kwh = 0.44 * sewerage_ave * (1/12) * pref_unit[pref_code-1][1]
    return kwh
"""


code_riverbankfield = """
def riverbankfield(name1,name2):
    '''
    河川データのfield統合
    input : 
        name1 : 入力field1
        name2 : 入力field2
    output :
        name : 統合したfield値
    '''
    if name1 != " ":
        name = name1
    else:
        if name2 != " ":
            name = name2
        else:
            name = " "
    return name
"""


code_riverbank = """
def riverbank(code_name,km):
    '''
    堤防敷・河川敷のポテンシャル推計
    input :
        code_name : 河川コードと河川名を結合した文字列
        km : 入力featureの長さ[km]
    output :
        result : featureごとのポテンシャル[kwh/y]
    '''
    df_index = df.index[(df['code_name'] == code_name)].tolist()
    df_index_len = len(df_index)
    if df_index_len == 0:
        print("Error_single" + code_name)
    elif df_index_len == 1:
        result = df["kwh_per_km"][df_index[0]] * km
    else:
        print("Error_multi" + code_name)
    return result
"""


code_coast = """
def coast(citycode):
    '''
    海岸のポテンシャル量推計
    input :
        citycode : 市区町村コード
    output :
        val : featureごとのポテンシャル[kwh/y]
    '''
    # 都道府県コード取得
    if citycode == " ":
        i = 47
    else:
        pref = citycode[0:2]
        i = int(pref) - 1
    # 都道府県ごとのunit取得
    if 0 <= i <= 46:
        unit = pref_unit[i][1]
    else:
        unit = pref_unit[47][1]
    val = unit * 100 * 3.82 * (1/12)
    return val
"""


def RiceField(dataframe):
    """
    田・その他農用地のメッシュ別のポテンシャル推計において使用
    input :
        dataframe : csvをdataframeとして入力
    output :
        val : featureごとののポテンシャル量
    """
    #都道府県コード取得
    if dataframe['citycode'] == " ":
        i = 47
    else:
        pref = dataframe['citycode']
        pref = pref[:2]
        i = int(pref) - 1
    #都道府県ごとのunit取得
    if 0 <= i <= 46:
        unit = pref_unit[i][1]
    else:
        unit = pref_unit[47][1]
    #土地利用種で面積割合が変わる
    factor = {100:80,200:40}
    use = dataframe['土地利用種']
    val = unit * 100*100 * (factor[use]/100) * (1/16)
    return val


code_abandoned = """
def abandoned(city):
    '''
    耕作放棄地のポテンシャル量推計
    input :
        city : 市区町村コード
    output :
        val : featureごとのポテンシャル[kwh/y]
    '''
    #都道府県コード取得
    if city == " ":
        i = 47
    else:
        pref = city[0:2]
        i = int(pref) - 1
    #都道府県ごとのunit取得
    if 0 <= i <= 46:
        unit = pref_unit[i][1]
    else:
        unit = pref_unit[47][1]
    val = unit * 100 * 100 * 0.30 * (1/12)
    return val
"""


# 変数の設定 ===========================================
# 地域別発電量係数（都道府県別）
pref_unit = [["01",1150],["02",1105],["03",1137],["04",1160],["05",1095],["06",1143],["07",1150],["08",1192],["09",1188],["10",1240],
             ["11",1198],["12",1188],["13",1134],["14",1208],["15",1118],["16",1118],["17",1118],["18",1140],["19",1339],["20",1221],
             ["21",1285],["22",1301],["23",1278],["24",1272],["25",1153],["26",1160],["27",1208],["28",1246],["29",1192],["30",1285],
             ["31",1127],["32",1124],["33",1259],["34",1282],["35",1217],["36",1285],["37",1275],["38",1294],["39",1339],["40",1233],
             ["41",1233],["42",1253],["43",1275],["44",1221],["45",1339],["46",1307],["47",1304],["48",1215]]


#　7.推計===============================================
logger.info('7. Estimating REpot...')
try:
    # 公民館================================================
    logger.info('7.1 processing Hall...')
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(publichall)
    # 取得したpathより，全shapeのmergeと座標変換を行う
    publichall_pro = IntegrateShapes(files, "publichall", True)
    # 公民館と集会施設を抽出
    publichall_selected = Extract(publichall_pro,"P05_002 = '4' or P05_002 = '5'","")
    # 公民館，集会施設の１施設あたりの平均面積を総務省，公共施設状況経年比較表2017を参照し，算出
    #  単位はm2, 全国の総延床面積[m2]　/ 全国の公民館数[個]
    kominkan_ave = 9532424 / 13055
    syukai_ave = 14300815 / 164768
    # 各施設のポテンシャル量を推計
    #  code_publichallで定義したpublichall関数を使用
    publichall_selected = CalculateField(publichall_selected, "publichall", "DOUBLE", "publichall(!P05_001!,!P05_002!)", code_publichall)
    #　各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    publichall_join = publichall_selected.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(publichall_selected, mesh, publichall_join, "", "", "","INTERSECT")
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(publichall_join, "publichall", "") 
except Exception as e:
    logger.error('Error!!! Check 7.1 processing Hall, please!')
    logger.error(e)


try:
    # 体育館================================================
    logger.info('7.2 processing gym...')
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    gym_pro = os.path.join(calculate_path, "gym_pro.shp")
    arcpy.management.Project(gym, gym_pro, 6668)
    # 体育館データだけを抽出
    gym_select = Extract(gym_pro, "P27_004 = '03109'", "")
    # 学校体育館と重複するものを取り除く
    #  code_gymCheckerで定義したgymChecker関数で学校体育館なら0, それ以外には1のフラグをつける
    gym_flag = CalculateField(gym_select, "gym_flag", "DOUBLE", "gymChecker(!P27_005!)",code_gymChecker)
    #  gym_flag==1のものを抽出
    gym_extract = Extract(gym_flag, "gym_flag = 1", "")
    # 体育館の１施設あたりの平均面積を総務省，公共施設状況経年比較表2017を参照し，算出
    #  単位はm2, 全国の総延床面積[m2]　/ 全国の体育館数[個]
    gym_ave = 15554166 / 6557
    # 各体育館のポテンシャル量を推計
    #  code_gymで定義したgym関数を使用
    gym_extract = CalculateField(gym_extract, "gym", "DOUBLE", "gym(!P27_001!)", code_gym)
    #　各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    gym_join = gym_extract.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(gym_extract, mesh, gym_join, "", "", "","INTERSECT")
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(gym_join, "gym", "") 
except Exception as e:
    logger.error('Error!!! Check 7.2 processing gym, please!')
    logger.error(e)


try:
    # 学校===================================================
    logger.info('7.3 processing school...')
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    school_pro = os.path.join(calculate_path, "school_pro.shp")
    arcpy.management.Project(school, school_pro, 6668)
    # 学校の１施設あたりの平均面積を文部科学統計要覧（h23年版のh18年のデータ）を参照し，算出
    # 「文部科学統計要覧」（文部科学省） （リンク）を加工して作成
    #  単位はm2, 全国の総延床面積[m2]　/ 全国の学校数[個]
    """
    field name = "P29_004"
    "16001" = "小学校"
    "16002" = "中学校"
    "16003" = "中等教育学校"
    "16004" = "高等学校"
    "16005" = "高等専門学校"
    "16007" = "大学"
    """
    ave_16001 = 104174.778*1000 / 22878
    ave_16002 = 63842.565*1000 / 10992
    ave_16003 = 120.869*1000 / 27
    ave_16004 = 64681.841*1000 / 5385
    ave_16005 = 1856.026*1000 / 64
    ave_16007 = 62632.001*1000 / 744
    # 小中高等学校の計算(中等教育学校を含む)
    #   抽出
    some_school = Extract(school_pro, "P29_004 = '16001' or P29_004 = '16002' or P29_004 = '16003' or P29_004 = '16004'", "school")
    #   各施設のポテンシャル量を推計
    #    code_schoolで定義したschool関数を使用
    some_school = CalculateField(some_school, "school", "DOUBLE", "school(!P29_001!,!P29_004!)", code_school)
    #　 各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    some_school_join = some_school.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(some_school, mesh, some_school_join, "", "", "","INTERSECT")
    #   featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(some_school_join, "school", "")
    # 大学の計算(高等専門学校を含む)
    #   抽出
    univ = Extract(school_pro, "P29_004 = '16005' or P29_004 = '16007'", "univ")
    #   位置が重複する大学が存在したため，緯度経度と大学名が一致していれば1つにまとめる
    univ_diss = univ.rstrip('.shp') + '_meshjoin.shp'
    univ = CalculateField(univ, "pref", "TEXT", "!P29_001!", "")
    univ = CalculateField(univ, "school_id", "TEXT", "!P29_004!", "")
    arcpy.Dissolve_management(univ, univ_diss, ["P29_005","X", "Y"], [["pref", "First"],["school_id", "First"]])
    #   各施設のポテンシャル量を推計
    #    code_univで定義したuniv関数を使用
    univ_diss = CalculateField(univ_diss, "univ", "DOUBLE", "univ(!FIRST_pref!,!FIRST_scho!)", code_univ)
    #　 各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    univ_join = univ_diss.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(univ_diss, mesh, univ_join, "", "", "","INTERSECT")
    #   featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(univ_join, "univ", "")
except Exception as e:
    logger.error('Error!!! Check 7.3 processing school, please!')
    logger.error(e)


try:
    # 公共下水=================================================
    logger.info('7.4 processing sewerage...')
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(sewerage)
    # P22bというファイルだけを抜き出す
    files_b = [file for file in files if "P22b" in file]
    # 取得したpathより，全shapeのmergeと座標変換を行う
    sewerage_pro = IntegrateShapes(files_b, "sewerage", False)
    # 公共下水処理場の平均敷地面積を算出
    #  環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，公共下水の全国敷地面積を参照
    #  施設数は，公共下水処理場のpoint featureの数を使用
    #  単位はm2, 全国の総敷地面積[m2]　/ 全国の処理場数[個]
    count = arcpy.GetCount_management(sewerage_pro)
    count = int(count.getOutput(0))
    sewerage_ave = 83249*1000 / count
    #   各施設のポテンシャル量を推計
    #    code_sewerageで定義したsewerage関数を使用
    sewerage_pro = CalculateField(sewerage_pro, "sewerage", "DOUBLE", "sewerage(!P22b_001!)", code_sewerage)
    #　 各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    sewerage_join = sewerage_pro.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(sewerage_pro, mesh, sewerage_join, "", "", "","INTERSECT")
    #   featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(sewerage_join, "sewerage", "")
except Exception as e:
    logger.error('Error!!! Check 7.4 processing sewerage, please!')
    logger.error(e)


try:
    # 工場====================================================
    # 都市地域土地利用細分メッシュデータから工場を抜き出す
    #  downloodしたshapeファイルのpathを取得
    logger.info('7.5 processing factory...')
    files = glob.glob(factory)
    #  データ量が大きいので25個のfileごとにmergeする
    #   files数をcount
    countFiles = len(files)
    step = 25
    count = countFiles // step
    if count % step != 0:
        count += 1
    lulucs_factory = []
    logger.info("Merging factory LULC meshes...")
    for i in range(count):
        logger.info(f"Processing {i} of {count}...")
        # 25fileずつ、土地利用種0702を抽出して、マージと座標変換を行う
        files_i = files[i*step:(i+1)*step]
        factory_select_i = IntegrateExactShapes(files_i, f'tmp_lulc_factory_{i+1}', False, expression = "土地利用種 = '0702'", processname = "factory")
        # リストに変数名を追加
        lulucs_factory.append(factory_select_i)

    # 分割したshapeを結合
    lulc_factory = os.path.join(calculate_path, "lulc_factory.shp")
    arcpy.Merge_management(lulucs_factory, lulc_factory)
    # ポテンシャル推計
    #  工場メッシュに均等にポテンシャルを持たせる
    #  環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #  大規模工場43億kwh/y，中規模工場66億，小規模工場268億
    kwh_ave = Division(lulc_factory, (43+66+268)*(10**8)) 
    #  各メッシュにポテンシャル量を持たせる
    lulc_factory = CalculateField(lulc_factory, "factory", "DOUBLE", kwh_ave, "")
    #　各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    lulc_factory_join = lulc_factory.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(lulc_factory, mesh, lulc_factory_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    #  featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(lulc_factory_join, "factory", "")
except Exception as e:
    logger.error('Error!!! Check 7.5 processing factory, please!')
    logger.error(e)


try:
    # 工業団地================================================
    logger.info('7.6 processing industrial park...')
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(industrialpark)
    # mergeで不具合が出るため、field"L05_007"をdeleteする
    for file in files:
        arcpy.management.DeleteField(file, ["L05_002","L05_007","L05_008"])
    # 取得したpathより，全shapeのmergeと座標変換を行う
    industrialpark_pro = IntegrateShapes(files, "industrialpark", True)
    # industrialpark_proポリゴンと標準地域メッシュをインターセクト
    #   2分の1地域メッシュのKEY_CODEと設備容量を対応付ける
    inFeatures = [[industrialpark_pro,1],[mesh,2]] # industrialpark_proを切り取るのでランクを1に
    industrialpark_intersected = industrialpark_pro.rstrip('.shp') + '_intersect.shp'
    arcpy.Intersect_analysis(inFeatures, industrialpark_intersected)
    # インターセクト後の各ポリゴンの面積を算出
    industrialpark_intersected = GeoCalculateField(industrialpark_intersected,"area_m2","DOUBLE","AREA_GEODESIC","SQUARE_METERS")
    # csvに吐き出して，ポテンシャル量を算出する
    #  csvへ
    industrialpark_csv = industrialpark_intersected.rstrip(".shp") + ".csv"
    arcpy.CopyRows_management(industrialpark_intersected, industrialpark_csv)
    #  pandasで推計する
    df = pd.read_csv(industrialpark_csv, usecols=["KEY_CODE", "area_m2"], dtype={'KEY_CODE': object})
    #  単位面積当たりのポテンシャル量を推計(kwh/m2)
    #   環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #   工業団地42億kwh/y
    kwh_m2 = 42*(10**8) / sum(df['area_m2'])
    df["induspark"] = df["area_m2"] * kwh_m2
    #  pandasでKEY_CODEごとにsummary
    df = df[["KEY_CODE","induspark"]]
    df = df.groupby("KEY_CODE").sum()
    df = df.reset_index()
    # 結果としてcsvに出力
    industrialpark_outcsv = os.path.join(output_path, "induspark_summary.csv") 
    df.to_csv(industrialpark_outcsv)
except Exception as e:
    logger.error('Error!!! Check 7.6 processing industrial park, please!')
    logger.error(e)


try:
    # 最終処分場==========================================================
    logger.info('7.7 processing indu_final...')
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(disposal)
    # General(一般廃棄物)とIndustrial(産業廃棄物)を分類する
    files_general = [file for file in files if "GeneralWasteDisposalFacilities" in file]
    files_industrial = [file for file in files if "IndustrialWasteDisposalFacilities" in file]
    # 一般廃棄物のポテンシャル推計
    #  うまくmergeできないので，不必要なfieldを除去する
    for file_general in files_general:
        arcpy.management.DeleteField(file_general, ["P15_005","P15_006","P15_007","P15_009","P15_010"])
    #  全shapeのmergeと座標変換を行う
    generaldisposal_pro = IntegrateShapes(files_general, "generaldisposal", True)
    #  最終処分場を抽出
    generalfinal = Extract(generaldisposal_pro, "P15_003 = '7'","")
    #  ポテンシャル推計
    #   処分場ごとに均等にポテンシャルを持たせる
    #   環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #   一般廃棄物の最終処分場45億kwh/y
    kwh_ave = Division(generalfinal, 45*(10**8)) 
    #  各メッシュにポテンシャル量を持たせる
    generalfinal = CalculateField(generalfinal, "gene_final", "DOUBLE", kwh_ave, "")
    #　各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    generalfinal_join = generalfinal.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(generalfinal, mesh, generalfinal_join, "", "", "","INTERSECT")
    #  featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(generalfinal_join, "gene_final" ,"")
    # 産業廃棄物のポテンシャル推計
    #  全shapeのmergeと座標変換を行う
    industrialdisposal_pro = IntegrateShapes(files_industrial, "industrialdisposal", True)
    #  最終処分場を抽出
    industrialfinal = Extract(industrialdisposal_pro, "P15_017 = '2'","")
    #  ポテンシャル推計
    #   処分場ごとに均等にポテンシャルを持たせる
    #   環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #   産業廃棄物安定型55億kwh/y，管理型37億kwh/y
    kwh_ave = Division(industrialfinal, (55+37)*(10**8)) 
    #  各メッシュにポテンシャル量を持たせる
    industrialfinal = CalculateField(industrialfinal, "indu_final", "DOUBLE", kwh_ave, "")
    #　各pointデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    industrialfinal_join = industrialfinal.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(industrialfinal, mesh, industrialfinal_join, "", "", "","INTERSECT")
    #  featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(industrialfinal_join, "indu_final" ,"")
except Exception as e:
    logger.error('Error!!! Check 7.7 processing indu_final, please!')
    logger.error(e)

try:
    # 河川敷・堤防敷===============================================================================
    logger.info('7.7 processing riverbank...')
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(riverbank)
    # streamというファイルだけを抜き出す
    files_stream = [file for file in files if "Stream" in file]
    # うまくmergeできないので，不必要なfieldを除去する
    for file_stream in files_stream:
        arcpy.management.DeleteField(file_stream, ["W05_006","W05_007","W05_008","W05_009","W05_010"])
    # 全shapeのmergeと座標変換を行う
    riverbank_pro = IntegrateShapes(files_stream, "riverbank", True)
    # merege前の各shapeのfield名が一致していないため揃える
    #  code_riverbankfieldで定義した，riverbankfield関数を使用
    riverbank_pro = CalculateField(riverbank_pro,"name","TEXT","riverbankfield(!W05_004!,!河川名!)",code_riverbankfield)
    riverbank_pro = CalculateField(riverbank_pro,"rank","TEXT","riverbankfield(!W05_003!,!区間種別!)",code_riverbankfield)
    riverbank_pro = CalculateField(riverbank_pro,"classcode","TEXT","riverbankfield(!W05_001!,!水系コード!)",code_riverbankfield)
    riverbank_pro = CalculateField(riverbank_pro,"rivercode","TEXT","riverbankfield(!W05_002!,!河川コード!)",code_riverbankfield)
    # 今回の対象である一級河川を抽出
    riverbank_1stclass = Extract(riverbank_pro,"rank = '1' or rank = '2' or rank = '5' or rank = '6'","")
    # いらないかもしれない→arcpy.Dissolve_management(inF, outF, ["rivercode", "name"], [["", "FIRST"],["","FIRST"]])
    # さらに河川を絞るためにclasscodeとnameを連結したcode_nameフィールドを作成
    riverbank_1stclass = CalculateField(riverbank_1stclass,"code_name","TEXT","!classcode!+!name!","")
    # 事前準備したcsvでもcode_name列を作成する
    df = pd.read_csv(riverbank_prepared_csv, encoding="utf-8")
    df["code_name"] = df['region_suikei'].astype(str) + df['rivername']
    # riverbank_1stclassの中からdfの"code_name"と一致するものだけを抽出する
    #  抽出のための条件式を作成する
    code_name_unique = df["code_name"].unique()
    expression = ""
    for name in code_name_unique:
        expression += "code_name = '" + name +  "' or "
    expression = expression.rstrip(" or ")
    #  抽出
    riverbank_1stclass = Extract(riverbank_1stclass,expression,"")
    # 河川データをdissolveする
    riverbank_dissolve = riverbank_1stclass.rstrip(".shp") + "_diss.shp"
    arcpy.Dissolve_management(riverbank_1stclass, riverbank_dissolve, ["code_name"])
    # インターセクトする
    inFeatures = [[riverbank_dissolve, 1],[mesh, 2]]
    riverbank_intersect = riverbank_dissolve.rstrip(".shp") + "_inter.shp"
    arcpy.Intersect_analysis(inFeatures, riverbank_intersect)
    # 河川長を求める
    riverbank_intersect = GeoCalculateField(riverbank_intersect,"line_km","DOUBLE","LENGTH_GEODESIC","KILOMETERS")
    # ポテンシャル量を算出する
    #  環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #  堤防敷・河川敷22億kwh/y
    #  dfの下準備を行う(河川ごとに人口化水際線の長さでポテンシャルを按分)
    df["arti_km"] = df["total_km"] * df["artificial"]/100
    df["kwh"] = 22*10**8 * (df["arti_km"]/df["arti_km"].sum())
    #  各河川ごとの単位長さ当たりのポテンシャル量[kwh/y/km]を求める
    df["kwh_per_km"] = df["kwh"] / df["total_km"]
    #  code_riverbankで定義したriverbank関数を使用
    riverbank_intersect = CalculateField(riverbank_intersect,"riverbank","DOUBLE","riverbank(!code_name!,!line_km!)",code_riverbank)
    #  featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(riverbank_intersect, "riverbank" ,"")
except Exception as e:
    logger.error('Error!!! Check 7.8 processing river bank, please!')
    logger.error(e)


try:
    # 駅======================================================================================================
    logger.info("7.8 processing station...")
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    station_pro = os.path.join(calculate_path, "station_pro.shp")
    arcpy.management.Project(station, station_pro, 6668)
    # 2017年度で，JRとPR(私鉄)に分類して，ポテンシャルを算出する
    #  JR(在来線＋新幹線)と私鉄（公営＋民営＋第三セクター）
    #  field名"S12_005"＝（1と2）（3と4と5）
    #  抽出
    JR = Extract(station_pro,"S12_030 = 1 and (S12_005 = 1 or S12_005 = 2)","station_JR")
    PR = Extract(station_pro,"S12_030 = 1 and (S12_005 = 3 or S12_005 = 4 or S12_005 = 5)","station_PR")
    #　各lineデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    #   結合方法はHAVE_THEIR_CENTER_INが望ましいが、エラーが生じるためINTERSECT(ArcGISpro上では可能だった)
    JR_join = JR.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(JR, mesh, JR_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    PR_join = PR.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(PR, mesh, PR_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    # csvに出力し，pandasで処理する
    JR_csv = JR_join.rstrip(".shp") + ".csv"
    arcpy.CopyRows_management(JR_join, JR_csv)
    PR_csv = PR_join.rstrip(".shp") + ".csv"
    arcpy.CopyRows_management(PR_join, PR_csv)
    # pandasで読み込む
    for station in [JR_csv, PR_csv]:
        df = pd.read_csv(station,encoding="utf-8")
        # field名の変換と，不要なfieldの除去
        #  field名変換
        df = df.rename(columns={"S12_001":"station","S12_002":"company","S12_003":"rail"})
        #  2011~2017年度ごとの重複コード(d)，データ有無コード(u)，乗降客数(p)のfield名の変換準備
        before_change = []
        after_change = []
        year = 2011
        for i in range(6, 31, 4):
            dupli = "S12_0" + str(i).zfill(2)
            umu = "S12_0" + str(i+1).zfill(2)
            pa = "S12_0" + str(i+3).zfill(2)
            before_change.append(dupli)
            before_change.append(umu)
            before_change.append(pa)
            d = "d" + str(year)
            u = "u" + str(year)
            p = "p" + str(year)
            after_change.append(d)
            after_change.append(u)
            after_change.append(p)
            year += 1
        #  field名変換
        for i in range(len(before_change)):
            df = df.rename(columns={before_change[i]:after_change[i]})
        #  不要なfieldの除去
        remove_field = [col for col in df.columns if "S12" in col]
        df = df.drop(remove_field,axis='columns')
        # 2017年に重複コード(d)!=1を省く
        df_index = df.index[(df['d2017'] != 1)].tolist()
        df = df.drop(df_index)
        # 7年間の平均乗降客数を算出する
        #  各駅で算出するための準備
        df_index = df.index.values
        d = ["d"+str(year) for year in range(2011, 2018)]
        u = ["u"+str(year) for year in range(2011, 2018)]
        p = ["p"+str(year) for year in range(2011, 2018)]
        #  7年間平均のデータ保存先の作成
        df["data_umu"] = 0
        df["p_ave"] = 0
        #  平均計算
        for index in df_index:
            d_index = [df.at[index, col] for col in d]
            u_index = [df.at[index, col] for col in u]
            p_index = [df.at[index, col] for col in p]
            result = passenger_ave(d_index,u_index,p_index)
            df.at[index,"data_umu"] = result[0]
            df.at[index,"p_ave"] = result[1]
        df = df[["KEY_CODE", "data_umu", "p_ave"]]
        # data_umu=0はnodata，data_umu=1はデータあり，data_umu=2はデータなし
        # data_umu = 1を抽出
        df = df.query("data_umu == 1")
        # JR,PR,どちらでも平均乗降客数の合計値を取る
        passenger_sum = df["p_ave"].sum()
        # 乗降客1人当たりポテンシャルを計算する
        #  環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
        #  JR + PR = 50億kwh/y
        #  分けたいので報告書記載の面積から按分
        JR_area =109839*1000
        PR_area = 29009*1000
        sum_area = JR_area + PR_area
        if "JR" in os.path.basename(station):
            station_potential = 50*(10**8)*(JR_area/sum_area)
            #  乗降客1人当たりポテンシャル 
            potential_per_passenger = station_potential / passenger_sum
            # stationのポテンシャル量を算出
            df["JR"] = df["p_ave"] * potential_per_passenger
            #  KEY_CODEごとにsummary
            df = df.groupby('KEY_CODE').sum()
            df = df.reset_index()
            # outputとしてcsvに出力
            df = df[["KEY_CODE","JR"]]
            JR_outcsv = os.path.join(output_path, "JR_summary.csv") 
            df.to_csv(JR_outcsv)
        elif "PR" in os.path.basename(station):
            station_potential = 50*(10**8)*(PR_area/sum_area)
            #  乗降客1人当たりポテンシャル 
            potential_per_passenger = station_potential / passenger_sum
            # stationのポテンシャル量を算出
            df["PR"] = df["p_ave"] * potential_per_passenger
            #  KEY_CODEごとにsummary
            df = df.groupby('KEY_CODE').sum()
            df = df.reset_index()
            # outputとしてcsvに出力
            df = df[["KEY_CODE","PR"]]
            PR_outcsv = os.path.join(output_path, "PR_summary.csv") 
            df.to_csv(PR_outcsv)
except Exception as e:
    logger.error('Error!!! Check 7.9 processing stations, please!')
    logger.error(e)


try:
    # 道路=================================================================================================
    logger.info("7.10 processing road...")
    # 座標をGCS JCD2000（EPSGコード4612）を定義
    arcpy.DefineProjection_management(road, 4612)
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    road_pro = os.path.join(calculate_path, "road_pro.shp")
    arcpy.management.Project(road, road_pro, 6668)
    # road_proポリゴンと標準地域メッシュをインターセクト
    #   2分の1地域メッシュのKEY_CODEと設備容量を対応付ける
    inFeatures = [[road_pro,1],[mesh,2]] # road_proを切り取るのでランクを1に
    road_intersected = road_pro.rstrip('.shp') + '_intersect.shp'
    arcpy.Intersect_analysis(inFeatures, road_intersected)
    # インターセクト後の各ポリゴンの長さを算出
    road_intersected = GeoCalculateField(road_intersected,"line_m","DOUBLE","LENGTH_GEODESIC","METERS")
    # csvを出力し，pandasで処理する
    road_csv = road_intersected.rstrip(".shp") + ".csv"
    arcpy.CopyRows_management(road_intersected, road_csv)
    df = pd.read_csv(road_csv, usecols=["KEY_CODE", "line_m"], dtype={'KEY_CODE': object})
    #  単位長さ当たりのポテンシャル量を求め，ポテンシャル量を算出
    #   環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #   道路法面118億kwh/y，中央分離帯2億kwh/y
    kwh_m = (118+2)*10**8 / sum(df['line_m'])
    df["road"] = df["line_m"] * kwh_m
    #  pandasでKEY_CODEごとにsummary
    df = df[["KEY_CODE","road"]]
    df = df.groupby("KEY_CODE").sum()
    df = df.reset_index()
    # 結果としてcsvに出力
    road_outcsv = os.path.join(output_path, "road_summary.csv") 
    df.to_csv(road_outcsv)
except Exception as e:
    logger.error('Error!!! Check 7.10 processing road, please!')
    logger.error(e)


try:
    #土地利用細分メッシュデータ=====================================
    # downloodしたshapeファイルのpathを取得
    files = glob.glob(landuse)
    # データ量が大きいので30個のfileごとに処理する
    countFiles = len(files)
    step = 30
    count = countFiles // step
    if count % step != 0:
        count += 1

    # 海岸(土地利用細分メッシュデータを使用)=================================================================
    # landusesから土地利用種"1400"の海岸を抜き出す
    logger.info("7.11 processing Coast...")
    lulucs_coast = []
    logger.info("Merging coast LULC meshes...")
    for i in range(count):
        logger.info(f"Processing {i} of {count}...")
        # 30fileずつ、土地利用種1400を抽出して、マージと座標変換を行う
        files_i = files[i*step:(i+1)*step]
        coast_select_i = IntegrateExactShapes(files_i, f'tmp_lulc_coast_{i+1}', False, expression = "土地利用種 = '1400'", processname = "coast")
        # リストに変数名を追加
        lulucs_coast.append(coast_select_i)
    # coastsをmeregeする
    coast = os.path.join(calculate_path, "lulc_coast.shp")
    arcpy.Merge_management(lulucs_coast, coast)
    # 各メッシュデータに空間結合で2分の1地域メッシュのKEY_CODEと市区町村コードを持たせる
    coast_join = coast.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(coast, mesh, coast_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    # ポテンシャル量を算出
    #  code_coastで定義したcoast関数を使用
    coast_join = CalculateField(coast_join,"coast","DOUBLE","coast(!N03_007!)",code_coast)
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(coast_join, "coast" ,"")


    # ゴルフ場(土地利用細分メッシュデータを使用)==============================================================
    # landusesから土地利用種"1600"のゴルフ場を抜き出す
    logger.info("7.12 processing golf...")
    lulcs_golf = []
    logger.info("Merging golf LULC meshes...")
    for i in range(count):
        logger.info(f"Processing {i} of {count}...")
        # 30fileずつ、土地利用種1600を抽出して、マージと座標変換を行う
        files_i = files[i*step:(i+1)*step]
        golf_select_i = IntegrateExactShapes(files_i, f'tmp_lulc_golf_{i+1}', False, expression = "土地利用種 = '1600'", processname = "golf")
        # リストに変数名を追加
        lulcs_golf.append(golf_select_i)
    # golfsをmeregeする
    golf = os.path.join(calculate_path, "golf.shp")
    arcpy.Merge_management(lulcs_golf, golf)
    # ポテンシャル推計
    #  ゴルフ場ごとに均等にポテンシャルを持たせる
    #  環境省，令和元年度再生可能エネルギーに関するゾーニング基礎情報等の整備・公開等に関する委託業務報告書より，全国発電量を参照
    #  ゴルフ場13億kwh/y
    kwh_ave = Division(golf, 13*(10**8)) 
    #  各メッシュにポテンシャル量を持たせる
    golf = CalculateField(golf, "golf", "DOUBLE", kwh_ave, "")
    # 各メッシュデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    golf_join = golf.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(golf, mesh, golf_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(golf_join, "golf" ,"")


    #田・その他農用地(土地利用細分メッシュデータを使用)==============================================================
    # landusesから土地利用種"0100","0200"を抜き出す
    logger.info("7.13 processing ricefields...")
    logger.info("Merging ricefields LULC meshes...")
    lulcs_ricefield = []
    for i in range(count):
        logger.info(f"Processing {i} of {count}...")
        # 30fileずつ、土地利用種0100 or 0200を抽出して、マージと座標変換を行う
        files_i = files[i*step:(i+1)*step]
        ricefield_select_i = IntegrateExactShapes(files_i, f'tmp_lulc_ricefield_{i+1}', False, expression = "土地利用種 = '0100' or 土地利用種 = '0200'", processname = "ricefield")
        # リストに変数名を追加
        lulcs_ricefield.append(ricefield_select_i)
    # ricefieldsをmeregeする
    ricefield = os.path.join(calculate_path, "ricefield.shp")
    arcpy.Merge_management(lulcs_ricefield, ricefield)
    # 不具合が生じるため，行政区域と重なっている部分だけを切り取る
    ricefield_select = GeoExtract(ricefield,japan)
    # 各メッシュデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    logger.info("(heavy operation, eta 1-2 hours) spacially joinning ricefields & 500m mesh...")
    ricefield_join = ricefield.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(ricefield, mesh, ricefield_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    # pandasでポテンシャル量を算出する
    #  csvに出力する
    ricefield_csv = ricefield_join.rstrip(".shp") + ".csv"
    arcpy.CopyRows_management(ricefield_join, ricefield_csv)
    #  pandasでcsvを読み込む
    df = pd.read_csv(ricefield_csv,encoding='utf-8',dtype={'N03_007':str})
    df = df[['土地利用種','KEY_CODE','N03_007']]
    df = df.rename(columns={'N03_007':'citycode'})
    #  ricefield関数をdfに適用し，ポテンシャル量を推計
    df['ricefield'] = df.apply(RiceField,axis=1)
    df = df[["KEY_CODE", "ricefield"]]
    #  pandasでKEY_CODEごとにsummary
    df = df.groupby('KEY_CODE').sum()
    df = df.reset_index()
    # 結果としてcsvに出力
    ricefield_outcsv = os.path.join(output_path, "ricefield_summary.csv")
    df.to_csv(ricefield_outcsv)


    # 耕作放棄地(土地利用細分メッシュデータ,農業地域データを使用)==============================================================
    logger.info("7.14 processing abandoned farmland...")
    # 農業地域データを処理する
    #  階層が異なるため，pathを2つ設定
    agriculture1 = os.path.join(agriculture, "**\*.shp")
    agriculture2 = os.path.join(agriculture, "**\**\*.shp")
    files1 = glob.glob(agriculture1)
    files2 = glob.glob(agriculture2)
    # 全shapeのpathを統合
    agri_files = files1 + files2
    # "205.shp"とfile名にあるものを使用する
    files_205 = [file for file in agri_files if "205.shp" in file]
    # 取得したpathより，全shapeのmergeと座標変換を行う
    agriculture205 = IntegrateShapes(files_205, "agriculture", False)
    # landusesから土地利用種"0600"の荒れ地を抜き出す
    lulcs_abandoned = []
    for i in range(count):
        logger.info(f"Processing {i} of {count}...")
        # 30fileずつ、土地利用種0600を抽出して、マージと座標変換を行う
        files_i = files[i*step:(i+1)*step]
        abandoned_select_i = IntegrateExactShapes(files_i, f'tmp_lulc_abandoned_{i+1}', False, expression = "土地利用種 = '0600'", processname = "abandoned")
        # リストに変数名を追加
        lulcs_abandoned.append(abandoned_select_i)
    # abandonedsをmeregeする
    abandoned = os.path.join(calculate_path, "abandoned.shp")
    arcpy.Merge_management(lulcs_abandoned, abandoned)
    # 耕作放棄地を荒れ地と農業地域の重なっている部分とする
    abandoned_farmland = GeoExtract(abandoned,agriculture205)
    # 各メッシュデータに空間結合で2分の1地域メッシュのKEY_CODEを持たせる
    logger.info("(heavy operation) spacially joinning abandoned farmlands & 500m mesh...")
    abandoned_farmland_join = abandoned_farmland.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(abandoned_farmland, mesh, abandoned_farmland_join, "", "", "","INTERSECT") # HAVE_THEIR_CENTER_INを推奨。手元のarcpy環境では動作しなかったため、INTERSECTを利用。
    # 各施設のポテンシャル量を推計
    #  code_abandonedで定義したabandoned関数を使用
    abandoned_farmland_join = CalculateField(abandoned_farmland_join, "abandoned", "DOUBLE", "abandoned(!N03_007!)", code_abandoned)
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(abandoned_farmland_join, "abandoned", "")
except Exception as e:
    logger.error('Error!!! Check 7.11-14, please!')
    logger.error(e)


logger.info("Finished 13 calculate_sunlight_public.py")
