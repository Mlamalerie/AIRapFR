import os
def create_folder(where, name_new_folder=None):
    new_folder_path = f"{where}/{name_new_folder}/" if name_new_folder else f"{where}/"
    if not os.path.exists(new_folder_path):
        os.mkdir(new_folder_path)
    return new_folder_path
