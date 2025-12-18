from urdf2webots.importer import convertUrdfFile
import os
import json
import shutil
import subprocess
import proto_praser as proto
import stl_tool

def zenity_select_folder(title="Select Folder"):
    """Use Zenity to select a folder"""
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--directory', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Selection cancelled")
        return None
    except FileNotFoundError:
        print("Zenity not found. Please install: sudo apt-get install zenity")
        return None

Folder_Object = {'Dir': {}, 'File': []}
    
# ================== File Browser ==================
input_path = zenity_select_folder("Select Input Folder")

if not input_path:
    print("No folder selected. Exiting.")
    exit(1)

folder_name = input_path.split(r"/")[-1]
print("Selected Folder: ", folder_name)

# lookup all the files and folders in the input_path
for root, dirs, files in os.walk(input_path):
    rt = os.path.relpath(root, input_path)      # get the relative path from input_path
    if rt == '.':   # if the root is the input_path
        rt = ''
        for d in dirs:
            Folder_Object['Dir'][d] = {'Dir':{}, 'File':[]}
        Folder_Object['File'] = files
    else:   # if the root is not the input_path
        for d in dirs:
            temp = {d: {'Dir':[], 'File':[]} }
            Folder_Object['Dir'][rt]['Dir'].append(temp)
        Folder_Object['Dir'][rt]['File'] = files

# # debugging: print the Folder_Object
# try:
#     with open('Folder_Object.json', 'w') as f:
#         json.dump(Folder_Object, f)
# except Exception as e:
#     print(e)

file_name = list(filter(lambda x: ".urdf" in x,Folder_Object["Dir"]["urdf"]["File"]))[0]    # get the urdf file name
Urdf_File = os.path.join(input_path, "urdf", file_name ).replace("\\", "/")                 # get the urdf file path
mesh_path = os.path.join(input_path, "meshes").replace("\\", "/")                           # get the mesh path
texture_path = os.path.join(input_path, "textures").replace("\\", "/")                      # get the texture path

print("Select Output Folder: ")
output_path = zenity_select_folder("Select Output Folder")

if not output_path:
    print("No output folder selected. Exiting.")
    exit(1)

print("Selected Output Folder: ", output_path)

# setup mesh file and texture to relative path with the output_path
try:
# Copy the mesh_path folder and its contents to the output_path
    target_mesh_dir = os.path.join(output_path, "meshes_"+folder_name)
    shutil.copytree(mesh_path, target_mesh_dir)
    # Copy the texture_path folder and its contents to the output_path
    shutil.copytree(texture_path, os.path.join(output_path, "textures_"+folder_name))
    
    # NEW: 在複製完檔案後，立刻對目標資料夾執行減面
    stl_tool.generate_collision_meshes(target_mesh_dir, target_faces=500)
except Exception as e:
    print(e)

# ================== Convert URDF to PROTO ==================
# convert the urdf file to proto file
proto_Filename = file_name.replace(".urdf", ".proto").replace("_", "")          # remove the "_" in the filename
proto_Filename = os.path.join(output_path, proto_Filename).replace('\\', '/')   # replace the backslash to slash
l = convertUrdfFile(input = Urdf_File , output = output_path)                   # convert the urdf file to proto file

# read the output file and replace the mesh path to relative path
with open(proto_Filename, 'r', encoding='utf-8') as file:
    datas = file.readlines()
    # print(datas)
    try:
        for i in range(len(datas)):
            l = datas[i]
            if "url" in l:
                l = l.replace("\\", "/")
                if mesh_path in l:
                    # print(l)
                    l = l.replace(mesh_path, './meshes_'+folder_name)    # replace the mesh path to relative path
                    # l = l.replace
                    # print(l)
                datas[i] = l
    except Exception as e:
        print("error occurs:\t", e)

with open(proto_Filename, 'w', encoding='utf-8') as file:
    file.writelines(datas)

# ================== 載入 Proto Robot ==================
proto_bot = proto.proto_robot(proto_filename = proto_Filename)

# ================== 自動替換 Collision Mesh (修正版) ==================
print("--- 開始替換物理碰撞模型 ---")

# 1. [建立對照表] 找出所有視覺模型的 DEF 名稱對應的 STL 路徑
#    例如: { "Base": "package:/.../Base.STL", "L_Motor": "..." }
geometry_nodes = proto_bot.search("geometry")
def_map = {}

for geo in geometry_nodes:
    # 檢查這個 geometry 是否有定義 DEF (例如: "DEF Base Mesh")
    if geo.DEF and "DEF" in geo.DEF:
        # 解析 DEF 字串，取出名字 (例如 "Base")
        parts = geo.DEF.split()
        if len(parts) >= 2:
            def_name = parts[1] # 取得中間的名字
            
            # 找出裡面的 url
            url_props = geo.search("url")
            if url_props:
                # 儲存到對照表
                def_map[def_name] = url_props[0].content
                # print(f"Found visual def: {def_name} -> {def_map[def_name]}")

# 2. [執行替換] 找出 boundingObject 並替換掉 USE 引用
bounding_objects = proto_bot.search("boundingObject")

for bo in bounding_objects:
    # 狀況 A: boundingObject 是一個 property (例如: boundingObject USE Base)
    if isinstance(bo, proto.property):
        if "USE" in bo.content:
            # 取出被引用的名稱 (例如 "Base")
            used_def_name = bo.content.replace("USE", "").strip()
            
            # 如果這個名稱在我們的對照表裡，代表它是引用視覺模型
            if used_def_name in def_map:
                original_url = def_map[used_def_name]
                
                # 產生 collision 檔名 (不分大小寫替換)
                # 保持原始檔案的大小寫格式
                if ".STL" in original_url:
                    collision_url = original_url.replace(".STL", "_collision.STL")
                elif ".stl" in original_url:
                    collision_url = original_url.replace(".stl", "_collision.stl")
                else:  # .Stl or other variations
                    collision_url = original_url[:-4] + "_collision" + original_url[-4:]
                
                # 建構一個全新的 Mesh Node 來取代原本的 USE property
                # 目標結構: 
                # boundingObject Mesh {
                #   url "..."
                # }
                
                # 建立 Node: name="boundingObject", DEF="Mesh" (這樣會印出 "boundingObject Mesh {")
                new_node = proto.Node(name="boundingObject", parent=bo.parent, DEF="Mesh {", stage=bo.stage)
                
                # 建立 url property
                # 注意：這裡加上引號 " "
                if not collision_url.startswith('"'):
                    collision_url = f'"{collision_url}"'
                    
                new_url_prop = proto.property(name="url", parent=new_node, content=collision_url, stage=bo.stage + 1)
                new_node.add_child(new_url_prop)
                
                # 關鍵步驟：在父節點的 children 列表中，把舊的 property 換成新的 Node
                parent_node = bo.parent
                if bo in parent_node.children:
                    idx = parent_node.children.index(bo)
                    parent_node.children[idx] = new_node
                    print(f"  [成功] 替換 USE {used_def_name} -> 使用獨立 collision 檔")

    # 狀況 B: boundingObject 本身已經是 Node (直接定義 Mesh)
    elif isinstance(bo, proto.Node):
        # 這是您原本邏輯適用的情況，保留以防萬一
        url_props = bo.search("url")
        if url_props:
            url_prop = url_props[0]
            original_url = url_prop.content
            if "_collision" not in original_url.lower() and (".stl" in original_url.lower()):
                 # 保持原始檔案的大小寫格式
                 if ".STL" in original_url:
                     new_url = original_url.replace(".STL", "_collision.STL")
                 elif ".stl" in original_url:
                     new_url = original_url.replace(".stl", "_collision.stl")
                 else:  # .Stl or other variations
                     new_url = original_url[:-4] + "_collision" + original_url[-4:]
                 url_prop.content = new_url
                 print(f"  [成功] 更新 Mesh URL: {os.path.basename(original_url)} -> collision")

# ================== 結束替換 ==================
print("--- 碰撞模型替換完成 ---")

# ================== Solid Reference ==================
l = proto_bot.search("endPoint")

# search empty solid and remove some properties
for i in l:
    Reference_Template = proto.Node(name = "endPoint", parent = None, DEF = "SolidReference {")
    
    ## Reference Template:
    ## ==========================================
    ## SolidReference {
    ##   SFString solidName ""   # any string
    ## }
    ## ==========================================
    
    n = i.search("name") #search for name property
    name = ""
    
    if len(n) >= 1: #if name property is found
        name = n[0].content #get the name
    
    # check if the node is a solid and empty
    if "Solid" in i.DEF and "Empty" in name:
        name_object = i.search("name")
        if len(name_object) >= 1:
            name_object = name_object[0].content
        else:
            name_object = None
        
        if name_object and "Ref" not in name_object:
            # print
            i.DEF = "SolidReference {"
            i.children = []
            i.add_child(proto.property(name = "solidName", parent = i, content = name_object[:-1:]+"_Ref\"", stage = i.stage+1))

# ================== Motor Torque Setting ==================
l = proto_bot.search("RotationalMotor")     # search for RotationalMotor node

for i in l:
    t = i.search("maxTorque")
    Reference_Template = proto.property(name = "maxTorque", parent = t[0].parent, content = "0.001", stage = t[0].stage)
    if t[0].stage >6:
        temp = i
        proto_bot.set_current(t[0])
        proto_bot.cursor.update(Reference_Template)   # replace the maxTorque property with the Reference_Template
        proto_bot.set_current(temp)
    # t = i.search("maxTorque")   
    # print("content: ",t[0],"\tstage: ",t[0].stage, "\tparent name: ",t[0].parent.search("name")[0])

# save the proto file
proto_bot.save_robot(proto_Filename)
