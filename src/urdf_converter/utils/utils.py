import subprocess

def zenity_select_folder(title="Select Folder", args = ['zenity', '--file-selection', '--directory', '--title']):
    """Use Zenity to select a folder"""
    try:
        result = subprocess.run(
            args=args+[title],
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