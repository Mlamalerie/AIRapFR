import json
from data_lyrics import get_artist_from_query, get_all_songs_from_artist, write_songs_to_json, get_df_from_one_json_file
import pandas as pd

# print list of range of numbers (01, 02, 03, ..., 10, 11, 12, ..., 99, 100)
print(*[f"{i:02d}" for i in range(1, 101)], sep=", ")


def get_df_from_one_json_file(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        data = json.load(f)
    return pd.json_normalize(data)

result = get_artist_from_query("Mayo")
print()