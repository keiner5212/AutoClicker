import os

def get_file_name(directory):
    files = os.listdir(directory)
    if files:
        return files[0]
    else:
        return ""

file_name = get_file_name(os.path.dirname(os.path.abspath(__name__))+"\\dist" if os.name == "nt" else "/dist")
print(file_name)
