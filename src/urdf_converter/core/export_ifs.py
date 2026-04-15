import sys
import os
from urdf_converter.core.convert_collision_to_ifs import stl_to_ifs_str

def export_single_stl_to_ifs(stl_path, output_path=None):
    print(f"🔵 正在處理 STL: {stl_path}")
    
    # 呼叫既有的 stl_to_ifs_str 函數
    ifs_text = stl_to_ifs_str(stl_path)
    
    if not ifs_text:
        print("❌ 轉換失敗或檔案不存在")
        return
    
    # 如果沒有指定輸出路徑，預設輸出為同目錄下的 [原檔名]_ifs.txt
    if not output_path:
        base_name = os.path.splitext(os.path.basename(stl_path))[0]
        dir_name = os.path.dirname(stl_path)
        output_path = os.path.join(dir_name, f"{base_name}_ifs.txt")
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ifs_text)
        
    print(f"🎉 成功輸出 IFS 字串至: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_stl = sys.argv[1]
        output_txt = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        from urdf_converter.ui.ui_picker import zenity_select_file
        input_stl = zenity_select_file("Select STL File")
        if not input_stl:
            print("未選擇檔案，退出")
            sys.exit(1)
        output_txt = None
    
    export_single_stl_to_ifs(input_stl, output_txt)
