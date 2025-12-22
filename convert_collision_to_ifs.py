import re
import os
import trimesh
import numpy as np
import sys

def stl_to_ifs_str(stl_path, indent_level=6):
    """
    讀取 STL 並回傳 Webots IndexedFaceSet 的字串格式
    """
    if not os.path.exists(stl_path):
        print(f"  ❌ 找不到檔案: {stl_path}")
        return None

    # 1. 讀取網格
    mesh = trimesh.load(stl_path)
    
    # 2. 合併頂點 (關鍵：減少檔案大小並符合 IFS 結構)
    mesh.merge_vertices()
    
    # 3. 準備縮排
    indent = " " * indent_level
    sub_indent = " " * (indent_level + 2)

    # 4. 建構 coord Coordinate
    coord_str = f"{indent}coord Coordinate {{\n{sub_indent}point [\n"
    points_list = [f"{v[0]:.4f} {v[1]:.4f} {v[2]:.4f}" for v in mesh.vertices]
    coord_str += f"{sub_indent}  " + f"\n{sub_indent}  ".join(points_list)
    coord_str += f"\n{sub_indent}]\n{indent}}}"

    # 5. 建構 coordIndex
    index_str = f"{indent}coordIndex [\n"
    faces_list = [f"{f[0]}, {f[1]}, {f[2]}, -1" for f in mesh.faces]
    index_str += f"{sub_indent}  " + f"\n{sub_indent}  ".join(faces_list)
    index_str += f"\n{indent}]"

    # 6. 組合 IndexedFaceSet (注意：這裡不加 geometry 前綴，因為我們要替換掉 Mesh)
    ifs_block = f"""IndexedFaceSet {{
{indent}creaseAngle 1.0
{coord_str}
{index_str}
{indent[:-2]}}}"""
    
    return ifs_block

def process_proto_file(proto_file_path):
    print(f"🔵 正在處理 PROTO: {proto_file_path}")
    
    if not os.path.exists(proto_file_path):
        print("❌ PROTO 檔案不存在")
        return

    with open(proto_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    proto_dir = os.path.dirname(proto_file_path)

    # --- [關鍵修改] ---
    # 1. 抓取 Mesh { ... } 區塊
    # 2. 條件：url 必須包含 "_collision.STL"
    # 這樣可以確保只改到 bounding object，而不會動到 visual mesh
    pattern = re.compile(
        r'(Mesh\s*\{\s*url\s*\[\s*"([^"]+?_collision\.STL)"\s*\]\s*\})',
        re.IGNORECASE | re.DOTALL
    )

    count = 0

    def replacement_handler(match):
        nonlocal count
        full_match_text = match.group(1) # 整個 Mesh { ... }
        stl_relative_path = match.group(2) # 只有路徑
        
        stl_full_path = os.path.join(proto_dir, stl_relative_path)
        print(f"  🔍 發現 Bounding Mesh: {stl_relative_path}")
        
        ifs_text = stl_to_ifs_str(stl_full_path)
        
        if ifs_text:
            count += 1
            return ifs_text
        else:
            return full_match_text

    # 執行替換
    new_content = pattern.sub(replacement_handler, content)

    # 存檔
    if count > 0:
        backup_path = proto_file_path + ".bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  💾 已備份: {backup_path}")

        with open(proto_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"🎉 成功轉換 {count} 個 Bounding Objects！")
    else:
        print("⚪ 未發現任何符合條件的 _collision.STL。")

if __name__ == "__main__":
    # 設定您的 PROTO 檔案路徑
    # 範例路徑，請修改為您的實際路徑
    target_proto = "/home/starlee/data_ext/Projects/Webots/Model_Importing_test/protos/CorgiRobot_IFS.proto"
    
    # 也可以透過命令列傳入參數
    if len(sys.argv) > 1:
        target_proto = sys.argv[1]

    process_proto_file(target_proto)