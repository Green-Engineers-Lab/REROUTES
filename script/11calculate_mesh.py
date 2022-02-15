"""
標準地域メッシュ
2分の1地域メッシュデータの作成

"""


# 1.load packages==============================================================
import glob
import arcpy
import os
# for logging
import json
from logging import getLogger, config
logger = getLogger(__name__)


# 2.root_dirの設定==============================================================
root_dir = r"C:\Users\GE\Documents\REROUTES-main"


# Logの設定 ===================================================================
with open(os.path.join(root_dir, 'script/log_config.json'), 'r') as f:
    log_conf = json.load(f)
logfname = os.path.join(root_dir, "log", f"log_11_calculate_mesh.log")
if not os.path.isdir(os.path.join(root_dir, "log")):
    os.makedirs(os.path.join(root_dir, "log"))
if os.path.isfile(logfname):
    os.remove(logfname)
log_conf["handlers"]["fileHandler"]["filename"] = logfname
config.dictConfig(log_conf)
logger.info('Start 11calculate_mesh.py program...')


# 3.pathの設定==================================
# download先に合わせる
logger.info('3. path setting...')
mesh_path = os.path.join(root_dir, "download\mesh")
# 処理途中で生じる生成物の保存先
calculate_path = os.path.join(root_dir, "calculate\mesh")
os.makedirs(calculate_path, exist_ok=True)
# 最終的なメッシュの保存先
output_path = os.path.join(root_dir, "result\mesh")
os.makedirs(output_path, exist_ok=True)

# 4.ファイル名一覧=================================================================
logger.info('4. file name setting...')
japan = os.path.join(root_dir, r"download\japan\N03-190101_GML\N03-19_190101.shp")


# 5.全標準地域メッシュの結合========================================================
try:
    logger.info('5. Merging all mesh data...')
    # 全標準地域メッシュファイルパスの取得
    mesh_path = os.path.join(mesh_path, "**\*.shp")
    files_mesh = glob.glob(mesh_path)
    # 全メッシュの結合
    mesh = os.path.join(calculate_path, "mesh500m.shp")
    arcpy.Merge_management(files_mesh, mesh)
except Exception as e:
    logger.error("Error!!! See 5, please!")
    logger.error(e)


# 6.標準地域メッシュの陸上部分だけを取得する
try:
    logger.info('6. Select terrestrial meshes...')
    # japanと重なるメッシュを取得
    mesh_land = os.path.join(calculate_path, "mesh500m_land.shp")
    mesh_selected = arcpy.management.SelectLayerByLocation(mesh, "INTERSECT", japan)
    arcpy.CopyFeatures_management(mesh_selected, mesh_land)
    # japanと空間結合し，市区町村コードを持たせる
    mesh_join = os.path.join(output_path, "mesh500m_land_city.shp")
    arcpy.SpatialJoin_analysis(mesh_land, japan, mesh_join, "", "", "", "HAVE_THEIR_CENTER_IN")
    # KEY_CODEを残して，他のfieldは除去
    drop_field = ["MESH1_ID","MESH2_ID","MESH3_ID","MESH4_ID","OBJ_ID","N03_001","N03_002","N03_003","N03_004"]
    arcpy.management.DeleteField(mesh_join, drop_field)
except Exception as e:
    logger.error("Error!!! See 6, please!")
    logger.error(e)

logger.info("Finished 11 calculate_mesh.py")
