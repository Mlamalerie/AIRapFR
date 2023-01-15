import os
from glob import glob

import pandas as pd

dir_path = "datasets/genius-1908-rohff"
COLUMNS_WE_NEED = ["artist", "lyrics"]


def clean_df(df):
    # raise error if df don't have the right columns
    if not {"artist", "lyrics"}.issubset(df.columns):
        raise ValueError("Columns are not correct in the dataframe")

    # manage type
    df['lyrics'] = df['lyrics'].astype(str)
    # int dtype={'id': 'Int64'} date, datetime ect

    # remove empty lyrics
    df = df.dropna(subset=['lyrics'])

    # remove duplicates
    df = df.drop_duplicates(subset=['lyrics'])
    return df


# load data from
def load_df_dataset(dir_path: str):
    # dir exists
    if not os.path.exists(dir_path):
        raise ValueError(f"Directory {dir_path} does not exist")

    query = f"{dir_path}/*.csv"
    # get just the csv file in the directory
    if files := glob(query):
        print(f"Loading {files[0]}")
        df = pd.read_csv(files[0])  # todo: keep juste columns we need
        return clean_df(df)
    return None

def load_df_all_datasets(base_dir_path : str):
    # dir exists
    if not os.path.exists(base_dir_path):
        raise ValueError(f"Directory {base_dir_path} does not exist")
    if files := glob(f"{base_dir_path}/*/*.csv"):
        print(f"Loading {len(files)} files")
        df = pd.concat([pd.read_csv(file_path) for file_path in files],ignore_index=True)
        return clean_df(df)
    return None

