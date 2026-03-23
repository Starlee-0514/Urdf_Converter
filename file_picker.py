# file_picker.py
import subprocess

def zenity_select_folder(title="Select Folder"):
    """
    使用 Zenity 选择文件夹
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
        print("Selection cancelled")
        return None
    except FileNotFoundError:
        print("Zenity not found. Please install: sudo apt-get install zenity")
        return None

def zenity_select_file(title="Select File"):
    """
    使用 Zenity 选择文件
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
        print("Selection cancelled")
        return None
    except FileNotFoundError:
        print("Zenity not found. Please install: sudo apt-get install zenity")
        return None

def zenity_select_path(title="Select Path", file_mode=False):
    """
    通用文件路径选择函数
    参数:
        title: 窗口标题
        file_mode: True 选择文件，False 选择文件夹
    """
    if file_mode:
        return zenity_select_file(title)
    else:
        return zenity_select_folder(title)