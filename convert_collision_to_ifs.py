import re
import os
import trimesh
import sys
import proto_praser as proto

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

def process_proto_file(proto_file_path, output_path=None):
    print(f"🔵 正在處理 PROTO: {proto_file_path}")
    
    if not os.path.exists(proto_file_path):
        print("❌ PROTO 檔案不存在")
        return

    proto_dir = os.path.dirname(proto_file_path)

    # --- [關鍵修改] ---
    # 1. 建立副本檔案
    proto_basename = os.path.basename(proto_file_path)
    default_copy_path = os.path.join(proto_dir, "copy_" + proto_basename)
    copy_proto_path = output_path if output_path else default_copy_path
    
    print(f"  📋 正在建立副本: {copy_proto_path}")
    
    with open(proto_file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(copy_proto_path, 'w', encoding='utf-8') as f:
        f.write(original_content)

    with open(copy_proto_path, 'r', encoding='utf-8') as f:
        copied_content = f.read()
    
    # 2. 從檔案名稱提取機器人名字
    # 移除 .proto 副檔名，並轉換為小寫
    robot_name = os.path.splitext(os.path.basename(copy_proto_path))[0]
    print(f"  🤖 機器人名字: {robot_name}")
    
    # 3. 抓取所有連結到 .stl/.STL 的 Mesh { ... } 區塊（不限 visual 或 bounding）
    pattern = re.compile(
        r'(Mesh\s*\{[\s\S]*?url\s*(?:\[\s*)?"([^"]+?\.stl)"(?:\s*\])?[\s\S]*?\})',
        re.IGNORECASE | re.DOTALL
    )

    count = 0
    failed = 0

    def replacement_handler(match):
        nonlocal count
        nonlocal failed
        full_match_text = match.group(1) # 整個 Mesh { ... }
        stl_relative_path = match.group(2) # 只有路徑
        
        stl_full_path = os.path.join(proto_dir, stl_relative_path)
        print(f"  🔍 發現 STL Mesh: {stl_relative_path}")
        
        ifs_text = stl_to_ifs_str(stl_full_path)
        
        if ifs_text:
            count += 1
            return ifs_text
        else:
            failed += 1
            return full_match_text

    # 執行替換
    new_content = pattern.sub(replacement_handler, copied_content)

    # 修改 PROTO 宣告名稱，使其與副本檔名一致
    proto_name_pattern = re.compile(r'(\bPROTO\s+)([A-Za-z_][A-Za-z0-9_]*)')
    new_content = proto_name_pattern.sub(rf'\1{robot_name}', new_content, count=1)

    # 同時處理可能的變數引用 (例如 $robot)
    new_content = re.sub(r'\$robot\b', f'${robot_name}', new_content, flags=re.IGNORECASE)

    with open(copy_proto_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # 使用既有 parser 進一步對齊 PROTO 內部名稱欄位
    try:
        parsed_copy = proto.proto_robot(proto_filename=copy_proto_path)
        parsed_copy.save_robot(copy_proto_path)
    except Exception as e:
        print(f"⚠️  名稱欄位二次對齊失敗，保留目前內容: {e}")

    # 存檔
    if count > 0:
        print(f"  💾 已寫入副本檔案: {copy_proto_path}")
        print(f"🎉 成功轉換 {count} 個 STL Mesh 為 IndexedFaceSet")
    else:
        print("⚪ 未發現任何符合條件的 .stl/.STL Mesh。")

    if failed > 0:
        print(f"⚠️  有 {failed} 個 STL 轉換失敗，已保留原始 Mesh 區塊。")

    return copy_proto_path

if __name__ == "__main__":
    # 優先使用 CLI 參數
    if len(sys.argv) > 1:
        target_proto = sys.argv[1]
    else:
        from ui_picker import zenity_select_file    
        # 透過 Zenity 選擇 PROTO 檔案
        target_proto = zenity_select_file("Select PROTO File")
        
        # 如果使用者取消選擇，則退出
        if not target_proto:
            print("未選擇 PROTO 檔案，退出")
            exit(1)

    process_proto_file(target_proto)