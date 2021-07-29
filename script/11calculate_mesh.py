"""
標準地域メッシュ
2分の1地域メッシュデータの作成

"""


# 1.load packages==============================================================
import glob
import arcpy
import os


# 2.root_dirの設定==============================================================
root_dir = r"E:\remap_test"


# 3.pathの設定==================================
# download先に合わせる
mesh_path = os.path.join(root_dir, "download\mesh")
# 処理途中で生じる生成物の保存先
calculate_path = os.path.join(root_dir, "calculate\mesh")
os.makedirs(calculate_path, exist_ok=True)
# 最終的なメッシュの保存先
output_path = os.path.join(root_dir, "result\mesh")
os.makedirs(output_path, exist_ok=True)

# 4.ファイル名一覧=================================================================
japan = os.path.join(root_dir, r"download\japan\N03-190101_GML\N03-19_190101.shp")


# 5.全標準地域メッシュの結合========================================================
# 全標準地域メッシュファイルパスの取得
mesh_path = os.path.join(mesh_path, "**\*.shp")
files_mesh = glob.glob(mesh_path)
# 全メッシュの結合
mesh = os.path.join(calculate_path, "mesh500m.shp")
arcpy.Merge_management(files_mesh, mesh)

# 6.標準地域メッシュの陸上部分だけを取得する
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