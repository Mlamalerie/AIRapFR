from glob import glob
import os
from tqdm import tqdm


if ini_files := glob('**/*.ini', recursive=True):
    print(f"Found {len(ini_files)} .ini files")
    # delete all .ini files
    for file in tqdm(ini_files):
        os.remove(file)
else:
    print("No .ini files found")


