from glob import glob
import os
from tqdm import tqdm


# get all .ini files in the projets (in all subfolders)
ini_files = glob('**/*.ini', recursive=True)

if len(ini_files) > 0:
    print(f"Found {len(ini_files)} .ini files")
    # delete all .ini files
    for file in tqdm(ini_files):
        os.remove(file)
else:
    print("No .ini files found")


