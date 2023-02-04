from glob import glob
import shutil
from data.load_corpus import CorpusDataManager
from tqdm import tqdm
import os
# multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
cdm = CorpusDataManager()
import json
import pandas as pd
from datetime import datetime

def get_df_from_one_json_file(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        data = json.load(f)
    return pd.json_normalize(data)


def get_df_from_all_json_files(dir_path):
    files = glob(f'{dir_path}/[Ll]yrics_*.json', recursive=True)
    dfs = [get_df_from_one_json_file(json_path) for json_path in files]
    return pd.concat(dfs, ignore_index=True)

def move_all_lyrics_json_file(where, artist_name=""):
    if files := glob(f'[Ll]yrics_{artist_name}*.json', recursive=True):
        for file_json in files:
            # move and check if file moved
            try:
                shutil.move(file_json, f"{where}/{file_json}")
            except Exception as e:
                raise Exception(f'Error move {file_json} : {e}')

    return where,files if files else []

def fix_dir_path(available_dir_path, artist_name=""):
    if artist_name == "lim":
        return None,None, None,0
    # verify if dir exists
    if not os.path.exists(available_dir_path):
        return None,None, None,0

    # verifiy if dir is empty (no json files)
    no_jsons_in_dir = False
    if not glob(f'{available_dir_path}/[Ll]yrics_*.json', recursive=True):
        no_jsons_in_dir = True

    # if dir is empty
    files_json_moved = []
    if no_jsons_in_dir:
        available_dir_path,files_json_moved = move_all_lyrics_json_file(available_dir_path, artist_name)
        if len(files_json_moved) > 0:
            print(f"> Moved {len(files_json_moved)} files to {available_dir_path}")


    # verify if dir is empty (no csv file)
    no_csvs_in_dir = False
    if not glob(f'{available_dir_path}/df_genius*.csv', recursive=True):
        no_csvs_in_dir = True

    # generate csv file if dir is empty
    if no_csvs_in_dir and not no_jsons_in_dir:
        # Get all json files from backup folder, and create a dataframe
        df_all_songs = get_df_from_all_json_files(available_dir_path)
        columns_for_sort = ["release_date_components.year"]
        if "album.name" in df_all_songs.columns:
            columns_for_sort.append("album.name")
        df_all_songs.sort_values(by=columns_for_sort, inplace=True)
        df_output_file = f"""{available_dir_path}/df_genius_{artist_name}_all_songs_{datetime.now().strftime("%Y%m")}.csv"""

        df_all_songs.to_csv(df_output_file, index=False)
        print(f"-> dataframe with {df_all_songs.shape[0]} songs, by {artist_name} : '{df_output_file}'")
    return artist_name, no_jsons_in_dir, no_csvs_in_dir,len(files_json_moved)

# multi-threading with ThreadPoolExecutor and tqdm (use .map())
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fix_dir_path, cdm.available_artists_ids_paths.get(id), name) for name, id in cdm.available_artists_names_ids.items()]
    for future in tqdm(as_completed(futures), total=len(futures)):
        a, no_jsons_in_dir, no_csvs_in_dir,m = future.result()
        if m or (not no_jsons_in_dir and no_csvs_in_dir):
            print(f"{a} : {no_jsons_in_dir} {no_csvs_in_dir} {m}")
        #print(f"Moved {len(files_json)} files to {where_dir_json}")


