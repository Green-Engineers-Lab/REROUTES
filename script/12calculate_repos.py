"""
REPOSデータの加工

"""
# 1.load packages=============================================================
import arcpy
import os
import pandas as pd
import glob
import gc


# 2.root_dirの設定==============================================================
root_dir = r"E:\remap_test"


# 3.pathの設定==============================================================
# download先のpathに合わせる
download_path = os.path.join(root_dir, r"download\repos")
# 処理途中で生じる生成物の保存先
calculate_path = os.path.join(root_dir, r"calculate\repos")
os.makedirs(calculate_path, exist_ok=True)
# 結果を出力したcsvの保存先
output_path = os.path.join(root_dir, r"result\repos_csv")
os.makedirs(output_path, exist_ok=True)


# 4.ファイル名設定===========================================================
# 陸上風力
onshore = os.path.join(download_path, "wind_land_i_s\wind_land_i_s.shp")
# 洋上風力
offshore = os.path.join(download_path, "wind_sea_i_s\wind_sea_i_s.shp")
# 住宅系太陽光
sunlight_sup = os.path.join(download_path, "sunlight_building_i_s\sunlight_building_i_s_sup.shp")
sunlight = os.path.join(download_path, "sunlight_building_i_s\sunlight_building_i_s.shp")
# 地熱（蒸気フラッシュ発電）
geoflash = os.path.join(download_path, "geo_steam150_i_s\geo_steam150_i_s.shp")
# 中小水力
river = os.path.join(download_path, "water_river_i_s\water_river_i_s.shp")
# 2分の1地域メッシュ
mesh = os.path.join(root_dir, "result\mesh\mesh500m_land_city.shp")
# 日本　行政区域
japan = os.path.join(root_dir, r"download\japan\N03-190101_GML\N03-19_190101.shp")


# 5.関数==============================================================================================================
# 関数
def Extract(inFeature,expression):
    '''
    属性選択を行い，選択したものを抽出
    input : 
        inFeature : 入力shape
        expression : 条件式(文字列で入力)
    output :
        outFeature : 出力shape
    '''
    # select by attribute & Copy
    inFeature_name = os.path.basename(inFeature)
    outFeature = os.path.join(calculate_path, inFeature_name.rstrip(".shp") + "_selected.shp")
    mesh_selected = arcpy.SelectLayerByAttribute_management(inFeature, "NEW_SELECTION", expression)
    arcpy.CopyFeatures_management(mesh_selected, outFeature)
    return outFeature


def GeoExtract(inFeature,selectFeature):
    '''
    属性選択を行い，選択したものを抽出
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
        codeblock : pythonコード（文字列で入力)
    output :
        inFeature : 計算後のfeature
    '''
    # add field
    arcpy.AddField_management(inFeature, newfield_name, type)
    # calculate field
    arcpy.CalculateField_management(inFeature, newfield_name, expression,"PYTHON3",codeblock)
    return inFeature


def GeoCalculateField(inFeature,newfield_name,type):
    '''
    新しいfieldを追加し，そのfieldに対して面積[km2]を計算
    input : 
        inFeature : 入力shape
        newfiled_name : 新しいfield名（10文字以下）
        type : 新しいfieldの型
        expression : 条件式(文字列で入力)
        codeblock : pythonコード（文字列で入力）
    output : 
        inFeature : 計算後のfeature
    '''
    # add field
    arcpy.AddField_management(inFeature, newfield_name, type)
    # calculate Geometry
    arcpy.CalculateGeometryAttributes_management(inFeature, [[newfield_name,"AREA_GEODESIC"]],"","SQUARE_KILOMETERS")
    return inFeature


def FeatureToPoint(inFeature,field,cellsize):
    '''
    featureをラスター化で細分化し，pointFeatureに直し，座標変換
    input : 
        inFeature : 入力shape
        field : ラスター化したときのvalueにあたるfield
        cellsize : ラスター化する1メッシュ当たりのサイズ[m]
    output :
        outFeature : 出力shape
    '''
    # feature to raster
    inFeature_name = os.path.basename(inFeature)
    outRaster = os.path.join(calculate_path, inFeature_name.rstrip(".shp") + ".tif")
    arcpy.FeatureToRaster_conversion(inFeature, field, outRaster, cellsize)
    # raster to point
    #  この際、field名が"Value"から"grid_code"に変換されることに注意
    inRaster = outRaster
    outFeature = inRaster.rstrip('.tif') + '_point.shp'
    arcpy.RasterToPoint_conversion(inRaster, outFeature, 'Value')
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    inFeature = outFeature
    outFeature = inFeature.rstrip('.shp') + '_pro.shp'
    arcpy.management.Project(inFeature, outFeature, 6668)
    return outFeature


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
        df = df.rename(columns={fieldname:newfieldname})
        fieldname = newfieldname
    df = df.groupby("KEY_CODE").sum()
    df = df.reset_index()
    df = df[["KEY_CODE",fieldname]]
    # 結果としてcsvに出力
    outTable = os.path.join(output_path, f"{fieldname}_summary.csv") 
    df.to_csv(outTable)
    return outTable


# codeblock
code_reclass = """
def reclass(windspeed):
    '''
    風速を0.1m/s刻みから0.5m/s刻みに変更する
    input :
        windspeed : 風速[m/s]*10
    output :
        reclass_windspeed : 変更後の風速[m/s]*10
    '''
    #10倍された値を戻す
    windspeed = windspeed / 10
    #少数第一位によってreclass
    int_windspeed = int(windspeed)
    decimal_windspeed = windspeed - int_windspeed
    if 0 <= decimal_windspeed < 0.5:
        reclass_windspeed = float(int_windspeed)
    elif 0.5 <= decimal_windspeed < 1:
        reclass_windspeed = float(int_windspeed) + 0.5
    reclass_windspeed = reclass_windspeed*10
    return reclass_windspeed
"""


code_onshore = """
def onshore(windspeed, area):
    '''
    陸上風力ポテンシャル[kwh/y]の推計
    input :
        windspeed : 風速[m/s]*10
        area : 面積[km2]
    output : 
        potential : メッシュごとのポテンシャル量[kwh/y]
    '''
    #風速8.5m/s以上なら8.5m/sと同じとして扱う
    if windspeed >= 85:
        windspeed = 85
    #陸上風力の設備利用率(風速:設備利用率)
    onshore_factor = { 55:20.7, 60:25.3 ,65:30.0, 70:34.6, 75:39.0, 80:43.1, 85:47.0 }
    #利用可能率と出力補正係数
    factor1 = 0.95
    factor2 = 0.90
    #風速ごとに異なる設備利用率を使用し推計(単位面積当たり設備容量10000kw/km2)
    potential = 10000 * area * 365 * 24 * onshore_factor[windspeed] / 100 * factor1 * factor2
    return potential
""" 


code_offshore = """
def offshore(windspeed):
    '''
    洋上風力ポテンシャル[kwh/y]の推計
    input :
        windspeed : 風速[m/s]*10
    output : 
        potential : メッシュごとのポテンシャル量[kwh/y]
    '''
    # 風速12.0m/s以上なら12.0m/sと同じとして扱う
    if windspeed >= 120:
        windspeed = 120
    # 洋上風力の設備利用率(風速:設備利用率)
    offshore_factor = { 65:31.2, 70:35.8, 75:40.3, 80:44.5, 85:48.3, 90:51.9, 95:55.2, 100:58.3, 105:61.0, 110:63.4, 115:65.5, 120:67.4 }
    # 利用可能率と出力補正係数
    factor1 = 0.90
    factor2 = 0.90
    # 風速ごとに異なる設備利用率を使用し推計
    # (単位面積当たり設備容量8000kw/km2)
    # (面積0.01km2)
    potential = 8000 * 0.01 * 365 * 24 * offshore_factor[windspeed] / 100 * factor1 * factor2
    return potential
"""


code_river = """
def river(kw):
    '''
    中小水力ポテンシャル[kwh/y]の推計
    input :
        kw :　設備容量[kw]
    output : 
        potential : メッシュごとのポテンシャル量[kwh/y]
    '''
    # 設備利用率の算出 (factor:年間時間*(設備利用率[%]/100))
    factor = (536.63 * (10**8)) /(890 * (10**4))
    potential = kw * factor
    return potential 
"""


code_geothermal = """
def geothermal(kw_km2,area):
    '''
    地熱発電ポテンシャル[kwh/y]の推計
    input :
        kw_km2 :　単位面積当たりの設備容量[kw/km2]
        area : 面積[km2]
    output : 
        potential : メッシュごとのポテンシャル量[kwh/y]
    '''
    #設備利用率の算出 (factor:年間時間*(設備利用率[%]/100))
    factor = (569*(10**8)) / (815*(10**4))
    potential = kw_km2 * area * factor
    return potential 
"""


try:
    # 6.陸上風力発電ポテンシャル推計============================================================
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    onshore_pro = os.path.join(calculate_path, "onshore_pro.shp")
    arcpy.management.Project(onshore, onshore_pro, 6668)
    # 風速5.5m/s以上のメッシュを抽出
    onshore_55 = Extract(onshore_pro, "gridcode >= 55")
    # 0.1m/s刻みの風速を0.5m/s刻みに分類する
    #   code_reclassで定義したreclass関数を使う
    #   風速の単位は0.1m/sで、整数値が格納されていることに注意
    onshore_55 = CalculateField(onshore_55, "speed_mod", "LONG", "reclass(!gridcode!)", code_reclass)
    # onshore_55ポリゴンと標準地域メッシュをインターセクト
    #   2分の1地域メッシュのKEY_CODEと風速を対応付ける
    inFeatures = [[onshore_55, 1], [mesh, 2]] #onshore_55を切り取るのでランクを1に
    onshore_intersected = onshore_55.rstrip('.shp') + '_intersect.shp'
    arcpy.Intersect_analysis(inFeatures, onshore_intersected)
    # インターセクト後の各ポリゴンの面積を算出
    onshore_intersected = GeoCalculateField(onshore_intersected, "area_km2", "DOUBLE")
    # 各ポリゴンごとにポテンシャル量を算出
    #   code_onshoreで定義したonshore関数を利用
    onshore_intersected = CalculateField(onshore_intersected, "onshore", "DOUBLE", "onshore(!speed_mod!,!area_km2!)", code_onshore)
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(onshore_intersected, "onshore", "")
except Exception as e:
    print(e)

try:
    # 7.洋上風力発電ポテンシャル推計============================================================
    # 風速6.5m/s以上のメッシュを抽出
    offshore_65 = Extract(offshore,"gridcode >= 65")
    # 0.1m/s刻みの風速を0.5m/s刻みに分類する
    #   code_reclassで定義したreclass関数を使う
    #   風速の単位は0.1m/sで、整数値が格納されていることに注意
    offshore_65 = CalculateField(offshore_65,"speed_mod","LONG","reclass(!gridcode!)",code_reclass)
    # 各ポリゴンごとにポテンシャル量を算出
    #   code_offshoreで定義したoffshore関数を利用
    offshore_65 = CalculateField(offshore_65,"offshore","DOUBLE","offshore(!speed_mod!)",code_offshore)
    # ポリゴンfeatureを100m幅のpointデータへと変換
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    #  field名が"grid_code"に変換されることに注意
    offshore_point = FeatureToPoint(offshore_65,"offshore",100)
    #　各pointデータに空間結合で最近傍な2分の1地域メッシュのKEY_CODEを持たせる
    offshore_join = offshore_point.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(offshore_point, mesh, offshore_join, "", "", "","CLOSEST_GEODESIC")
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(offshore_join,"grid_code", "offshore")
except Exception as e:
    print(e)


try:
    # 8.地熱発電ポテンシャル推計============================================================
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    geoflash_pro = os.path.join(calculate_path, "geoflash_pro.shp")
    arcpy.management.Project(geoflash, geoflash_pro, 6668)
    # geoflash_proポリゴンと標準地域メッシュをインターセクト
    #   2分の1地域メッシュのKEY_CODEと設備容量を対応付ける
    inFeatures = [[geoflash_pro,1],[mesh,2]] #geoflash_proを切り取るのでランクを1に
    geoflash_intersected = geoflash_pro.rstrip('.shp') + '_intersect.shp'
    arcpy.Intersect_analysis(inFeatures, geoflash_intersected)
    # インターセクト後の各ポリゴンの面積を算出
    geoflash_intersected = GeoCalculateField(geoflash_intersected,"area_km2","DOUBLE")
    # 各ポリゴンごとにポテンシャル量を算出
    #   code_geothermalで定義したgeothermal関数を利用
    geoflash_intersected = CalculateField(geoflash_intersected,"geoflash","DOUBLE","geothermal(!gridcode!,!area_km2!)",code_geothermal)
    # featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(geoflash_intersected,"geoflash","")
except Exception as e:
    print(e)

try:
    # 9.中小水力発電ポテンシャル推計============================================================
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    river_pro = os.path.join(calculate_path, "river_pro.shp")
    arcpy.management.Project(river, river_pro, 6668)
    # 各ポリゴンごとにポテンシャル量を算出
    #   code_riverで定義したriver関数を利用
    river_pro = CalculateField(river_pro, "river", "DOUBLE", "river(!設備容量!)",code_river)
    #　各lineデータに空間結合で中点が位置する2分の1地域メッシュのKEY_CODEを持たせる
    river_join = river_pro.rstrip('.shp') + '_meshjoin.shp'
    arcpy.SpatialJoin_analysis(river_pro, mesh, river_join, "", "", "","HAVE_THEIR_CENTER_IN")
    #　featureのtableデータをcsvに出力し，2分の1地域メッシュごとにsummary
    toCSV(river_join,"river","")
except Exception as e:
    print(e)


try:
    # 10.住宅系太陽光発電ポテンシャル推計============================================================
    # 住宅系太陽光shapeファイルの本体と補完を結合
    sunlight_building = os.path.join(calculate_path, "sunlight_building.shp")
    arcpy.Merge_management([sunlight,sunlight_sup], sunlight_building)
    # ポリゴンfeatureを100m幅のpointデータへと変換
    # 座標をGCS JCD2011（EPSGコード6668）に変換
    #  field名が"grid_code"に変換されることに注意
    #  500mメッシュを100mメッシュに25分割したため、ポテンシャル量が25倍になっていることに注意
    sunlight_point = FeatureToPoint(sunlight_building, "発電電力量", 100)
    # 陸上のpointを抽出するため，行政区域japanと重ねる
    sunlight_land = GeoExtract(sunlight_point, japan)
    # 400万pointずつ空間結合を行う(データ量が大きく支障をきたすため)
    #  point数をcount 
    countFeature = arcpy.GetCount_management(sunlight_land)
    countFeature = int(countFeature.getOutput(0))
    step = 4*(10**6)
    count = countFeature // step + 1
    sunlight_joins = []
    for i in range(0,count):
        # 400万pointずつselectして抽出
        sunlight_i = sunlight_land.rstrip('.shp') + f'_selected{i+1}.shp'
        sunlight_i_selected = arcpy.SelectLayerByAttribute_management(sunlight_land, "NEW_SELECTION", f"{step*i} <= pointid and pointid < {step*(i+1)}")
        arcpy.CopyFeatures_management(sunlight_i_selected, sunlight_i)
        # 空間結合でKEY_CODEを持たせる
        sunlight_i_join = sunlight_i.rstrip('.shp') + '_meshjoin.shp'
        arcpy.SpatialJoin_analysis(sunlight_i, mesh, sunlight_i_join, "", "", "","INTERSECT")
        # 出力結果のpathをリストに追加
        sunlight_joins.append(sunlight_i_join)
    # sunlight_joinsをdataframeに変換し、結合する
    for sunlight_i in sunlight_joins:
        # sunlight_joinsをcsvに変換する
        sunlight_i_csv = sunlight_i.rstrip(".shp") + ".csv"
        arcpy.CopyRows_management(sunlight_i, sunlight_i_csv)
        # sunlight_joinsをdataframeに読み込む
        df = pd.read_csv(sunlight_i_csv, encoding = "utf-8", usecols = ["KEY_CODE","grid_code"])
        if sunlight_joins.index(sunlight_i) == 0:
            df_merged = df
        else:
            df_merged = pd.concat([df_merged, df])
        gc.collect()
    # dataframeをKEY_CODEごとにsummary
    #  ここでgrid_codeを1/25する
    df_merged["building"] = df_merged["grid_code"] / 25
    df_merged = df_merged.groupby("KEY_CODE").sum()
    df_merged = df_merged.reset_index()
    df_merged = df_merged[["KEY_CODE","building"]]
    # dataframeをcsv保存
    dataframe = os.path.join(output_path, "building_summary.csv")
    df_merged.to_csv(dataframe)
except Exception as e:
    print(e)