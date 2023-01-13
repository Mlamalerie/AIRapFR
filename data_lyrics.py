import argparse
from datetime import datetime
from glob import glob
import json
import os
import shutil
import time
import re
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import lyricsgenius

from utils import create_dir, compare_str

GENIUS_API_TOKEN = "dj04TpKhldHudO8VnobaSSzXtuuZ2hbSgl1DW-1Jug6i1Tt33B0JjXhDzdAk6V7m"
genius = lyricsgenius.Genius(GENIUS_API_TOKEN)
genius

BACKUP_FOLDER_PATH = f"{os.path.dirname(__file__)}\data"

def get_artist_from_id(id):
    return genius.artist(id)
def get_artist_from_query(q: str):
    """
    Search a artist by name
    :param q:
    :param index:
    :return:
    """
    data = genius.search_artists(f'"{q}"')
    hits = data['sections'][0]['hits']
    if not len(hits) > 0:
        print(f"Artist not found for query: {q}")
        return None

    hit_first = hits[0]["result"]

    result = {
    }
    result["index"] = 0
    result["query"] = q
    result.update(hit_first)

    if compare_str(result["name"].lower(), q.lower()) < 0.9:
        for hit in hits:
            if compare_str(hit["result"]["name"], q.lower()) >= 0.9:
                result["query"] = q
                result["index"] = hits.index(hit)
                result.update(hit["result"])
                break

    print("Artist found : ", result)
    if ag := get_artist_from_id(int(result["id"])):
        if "artist" in ag.keys():
            result.update(ag["artist"])
    return result


# get all songs from artist
def get_all_songs_from_artist(artist_name, artist_id, try_how_many=10, sleep_sec=5, max_songs=None,
                              include_features=False):
    if try_how_many > 0:
        try:
            artist = genius.search_artist(artist_name=artist_name, artist_id=artist_id, max_songs=max_songs,
                                          include_features=include_features)
            return artist.songs
        except Exception as e:
            print(f"Error : {e}... att {sleep_sec}sec ⌛")
            try_how_many -= 1
            time.sleep(sleep_sec)
            return get_all_songs_from_artist(artist_name, artist_id, try_how_many, sleep_sec)
        return artist.songs
    else:
        return None


def write_songs_to_json(songs, overwrite=True):
    for song in songs:
        # filename_path = os.path.join(dir_path,f"lyrics_{song.id}_{artist_}_{title_}")
        song.save_lyrics(extension='json', overwrite=overwrite, ensure_ascii=False, sanitize=True, verbose=True)


def move_all_lyrics_json_file(where):
    if files := glob('[Ll]yrics_*.json', recursive=True):
        for file_json in files:
            shutil.move(file_json, f"{where}/{file_json}")
    return where


def get_df_from_one_json_file(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        data = json.load(f)
    return pd.json_normalize(data)


def get_df_from_all_json_files(dir_path):
    files = glob(f'{dir_path}/[Ll]yrics_*.json', recursive=True)
    dfs = [get_df_from_one_json_file(json_path) for json_path in files]
    return pd.concat(dfs, ignore_index=True)


# verify if artist query is already done
def is_query_already_done(query):
    with open("todo_scrap/queries_done.txt", encoding='utf-8') as f:
        for readline in f:
            line_strip = readline.strip()
            if line_strip.lower() == query.lower():
                return True
    return False


# add artist query to done list
def add_query_to_done_list(query):
    if not is_query_already_done(query):
        with open("todo_scrap/queries_done.txt", "a", encoding='utf-8') as f:
            f.write(f"{query}\n")


def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-qa', "--query-artist", help='The artist', required=False, default=None)
    parser.add_argument('-id', "--query-artist-id", help='The artist', required=False, default=None)
    parser.add_argument('-ow', "--overwrite", help='Overwrite lyrics files', required=False, default=True)
    argdict = vars(parser.parse_args())
    OVERWRITE = argdict['overwrite']
    QUERY_ARTIST_ID = argdict['query_artist_id']
    if QUERY_ARTIST_ID is None:
        QUERY_ARTIST = argdict['query_artist'] or input("> Artist name (query): ")

        # Get artist
        artist_found = get_artist_from_query(QUERY_ARTIST, index=0)
        if artist_found is None:
            return
    else:
        artist_found = get_artist_from_id(QUERY_ARTIST_ID) #todo verify if artist is found and dict is have correct key
        if artist_found is None:
            return
    ARTIST_GENIUS_ID = artist_found["id"]
    ARTIST_NAME = artist_found["name"]

    # Get all songs from artist
    songs = get_all_songs_from_artist(artist_name=ARTIST_NAME, artist_id=ARTIST_GENIUS_ID,
                                      include_features=False)
    if not songs:
        print(f"No songs found (query={QUERY_ARTIST})")
        return

    # Get all songs from artist
    where_dir_json = create_dir(BACKUP_FOLDER_PATH,
                                f"genius-{ARTIST_GENIUS_ID}-{re.sub('[^A-Za-z0-9é]+', '', ARTIST_NAME.lower())}")

    # write all songs to json files
    write_songs_to_json(songs, overwrite=OVERWRITE)

    # move all json files to backup folder
    where_dir_json = move_all_lyrics_json_file(where_dir_json)

    # Get all json files from backup folder, and create a dataframe
    df_all_songs = get_df_from_all_json_files(where_dir_json)
    columns_for_sort = ["release_date_components.year"]
    if "album.name" in df_all_songs.columns:
        columns_for_sort.append("album.name")
    df_all_songs.sort_values(by=columns_for_sort, inplace=True)
    df_output_file = f"""{where_dir_json}/df_genius_{re.sub('[^A-Za-z0-9]+', '', ARTIST_NAME.lower())}_all_songs_{datetime.now().strftime("%Y%m")}.csv"""

    df_all_songs.to_csv(df_output_file, index=False)
    print(f"-> dataframe with {df_all_songs.shape[0]} songs, by {ARTIST_NAME} : '{df_output_file}'")

    add_query_to_done_list(QUERY_ARTIST)  # done


if __name__ == "__main__":
    main()
