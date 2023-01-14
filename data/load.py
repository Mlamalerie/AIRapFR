from glob import glob
import pandas as pd
import numpy as np
import os
dir_path = "datasets/genius-1908-rohff"

# load data from
def load_df_dataset(dir_path: str):
    # dir exists
    if not os.path.exists(dir_path):
        raise ValueError(f"Directory {dir_path} does not exist")
    query = f"{dir_path}/*.csv"
    # get just the csv file in the directory
    if files := glob(query):
        print(f"Loading {files}")
        return pd.read_csv(files[0])
    return None

def load_df_all_datasets(base_dir_path : str):
    # dir exists
    if not os.path.exists(base_dir_path):
        raise ValueError(f"Directory {base_dir_path} does not exist")
    if files := glob(f"{base_dir_path}/*/*.csv"):
        df = pd.concat([pd.read_csv(file_path) for file_path in files],ignore_index=True)
        df = df.dropna(subset=['lyrics'])
        return df
    return None

