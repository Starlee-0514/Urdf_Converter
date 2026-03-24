"""
ui_picker.py
提供透過 Zenity UI 選擇檔案、資料夾和路徑的工具函數
"""
import subprocess
from typing import Optional

def zenity_select_folder(title: str = "Select Folder") -> Optional[str]:
    """
    使用 Zenity 選擇資料夾
    
    Args:
        title: 視窗標題
        
    Returns:
        選取的資料夾路徑，取消則返回 None
    """
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--directory', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("選擇已取消")
        return None
    except FileNotFoundError:
        print("未找到 Zenity。請安裝：sudo apt-get install zenity")
        return None


def zenity_select_file(title: str = "Select File") -> Optional[str]:
    """
    使用 Zenity 選擇單一檔案
    
    Args:
        title: 視窗標題
        
    Returns:
        選取的檔案路徑，取消則返回 None
    """
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("選擇已取消")
        return None
    except FileNotFoundError:
        print("未找到 Zenity。請安裝：sudo apt-get install zenity")
        return None


def zenity_select_path(title: str = "Select Path") -> Optional[str]:
    """
    使用 Zenity 選擇檔案或資料夾（不限類型）
    
    Args:
        title: 視窗標題
        
    Returns:
        選取的路徑，取消則返回 None
    """
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("選擇已取消")
        return None
    except FileNotFoundError:
        print("未找到 Zenity。請安裝：sudo apt-get install zenity")
        return None


def zenity_select_multiple_files(title: str = "Select Multiple Files", min_count: int = 1) -> list:
    """
    使用 Zenity 選擇多個檔案
    
    Args:
        title: 視窗標題
        min_count: 最少選擇的檔案數量
        
    Returns:
        選取的檔案路徑列表，取消則返回空列表
    """
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--multiple', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        paths = result.stdout.strip().split('\n')
        paths = [p.strip() for p in paths if p.strip()]
        
        if len(paths) < min_count:
            print(f"請至少選擇 {min_count} 個檔案")
            return []
        
        return paths
    except subprocess.CalledProcessError:
        print("選擇已取消")
        return []
    except FileNotFoundError:
        print("未找到 Zenity。請安裝：sudo apt-get install zenity")
        return []


def zenity_select_multiple_folders(title: str = "Select Multiple Folders", min_count: int = 1) -> list:
    """
    使用 Zenity 選擇多個資料夾
    
    Args:
        title: 視窗標題
        min_count: 最少選擇的資料夾數量
        
    Returns:
        選取的資料夾路徑列表，取消則返回空列表
    """
    try:
        result = subprocess.run(
            ['zenity', '--file-selection', '--directory', '--multiple', '--title', title],
            capture_output=True,
            text=True,
            check=True
        )
        paths = result.stdout.strip().split('\n')
        paths = [p.strip() for p in paths if p.strip()]
        
        if len(paths) < min_count:
            print(f"請至少選擇 {min_count} 個資料夾")
            return []
        
        return paths
    except subprocess.CalledProcessError:
        print("選擇已取消")
        return []
    except FileNotFoundError:
        print("未找到 Zenity。請安裝：sudo apt-get install zenity")
        return []


if __name__ == "__main__":
    # 測試用
    print("測試選擇資料夾...")
    folder = zenity_select_folder()
    if folder:
        print(f"選取的資料夾：{folder}")
    
    print("\n測試選擇檔案...")
    file = zenity_select_file()
    if file:
        print(f"選取的檔案：{file}")