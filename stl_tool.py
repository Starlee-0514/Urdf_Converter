import open3d as o3d
import os
import glob

def generate_collision_meshes(mesh_folder, target_faces=300):
    """
    遍歷指定資料夾，將所有 .stl 檔案生成 _collision.stl 版本
    """
    print(f"--- 開始處理網格減面: {mesh_folder} ---")
    # 搜尋所有 stl 檔案 (不分大小寫)
    files = []
    for ext in ["*.stl", "*.STL", "*.Stl"]:
        search_path = os.path.join(mesh_folder, "**", ext)
        files.extend(glob.glob(search_path, recursive=True))
    
    generated_files = []

    for input_path in files:
        # 跳過已經是 collision 的檔案 (不分大小寫)
        if "_collision" in input_path.lower():
            continue
        
        # 根據原始檔案的擴展名，生成相同大小寫的 collision 檔名
        if input_path.endswith(".STL"):
            output_path = input_path.replace(".STL", "_collision.STL")
        elif input_path.endswith(".stl"):
            output_path = input_path.replace(".stl", "_collision.stl")
        else:  # .Stl or other variations
            output_path = input_path[:-4] + "_collision" + input_path[-4:]
        
        # # 如果 collision 檔已經存在，就不重新算，節省時間
        # if os.path.exists(output_path):
        #     continue

        try:
            # 1. 讀取
            mesh = o3d.io.read_triangle_mesh(input_path)
            if len(mesh.triangles) <= target_faces:
                # 如果原本面數就很少，直接複製一份
                o3d.io.write_triangle_mesh(output_path, mesh)
                continue

            # 2. 減面 (Quadric Decimation)
            mesh_smp = mesh.simplify_quadric_decimation(target_number_of_triangles=target_faces)
            mesh_smp.compute_vertex_normals()
            
            # 3. 存檔
            o3d.io.write_triangle_mesh(output_path, mesh_smp)
            generated_files.append(output_path)
            print(f"已生成: {os.path.basename(output_path)} ({len(mesh_smp.triangles)} faces)")
            
        except Exception as e:
            print(f"處理 {os.path.basename(input_path)} 時發生錯誤: {e}")
            
    print(f"--- 減面完成，共生成 {len(generated_files)} 個新檔案 ---")

if __name__ == "__main__":
    # 測試用範例
    test_folder = r"/home/starlee/dev/ros2_ws/src/corgi_ros_control/protos/meshes_CorgiRobot"
    generate_collision_meshes(test_folder, target_faces=100)