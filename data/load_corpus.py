import os
import re
from glob import glob
from typing import Tuple

import pandas as pd


class CorpusDataManager():
    def __init__(self, base_dir_path="datasets", columns_we_need=None):

        if columns_we_need is None:
            columns_we_need = [
                "artist",
                'primary_artist.id',
                "lyrics",
                "id",
                "title",
                "album.name",
                "release_date_components.year",
                "artist_names",
                "featured_artists",
                "language"
            ]
        if not os.path.exists(base_dir_path):
            raise ValueError(f"Directory {base_dir_path} does not exist")

        self.base_dir_path = base_dir_path
        self.columns_we_need = columns_we_need
        self.available_artists_ids_names, self.available_artists_ids_paths = self.get_available_artists()
        self.available_artists_names_ids = {v: k for k, v in self.available_artists_ids_names.items()}

    def get_available_artists(self) -> Tuple[dict, dict]:
        if dirs := glob(f"{self.base_dir_path}/*"):
            return {
                os.path.basename(dir_path)
                .split("-")[1]: os.path.basename(dir_path)
                .split("-")[-1]
                for dir_path in dirs
            }, {
                os.path.basename(dir_path)
                .split("-")[1]: dir_path
                for dir_path in dirs
            }
        return None, None

    def get_id_by_artist_name(self, artist_name: str) -> int:
        artist_name = re.sub('[^A-Za-z0-9é]+', '', artist_name.lower())
        if artist_name in self.available_artists_names_ids:
            return self.available_artists_names_ids[artist_name]
        return None

    def _clean_df_lyrics(self, df):

        # raise error if df don't have the right columns
        if not {"artist", "lyrics"}.issubset(df.columns):
            raise ValueError("Columns are not correct in the dataframe")

        # remove empty lyrics
        df = df.dropna(subset=['lyrics'])

        # remove duplicates
        df = df.drop_duplicates(subset=['lyrics'])

        # manage type
        df['lyrics'] = df['lyrics'].astype(str)
        df['language'] = df['language'].astype(str)
        df['artist'] = df['artist'].astype(str)
        df['title'] = df['title'].astype(str)
        df['album.name'] = df['album.name'].astype(str)
        df['artist_names'] = df['artist_names'].astype(str)
        # int dtype={'id': 'Int64'} date, datetime ect

        # select columns we need
        if self.columns_we_need:
            df = df[self.columns_we_need]
        return df

    def _get_df_dataset_by_dirpath(self, dir_path: str) -> pd.DataFrame:
        # dir exists
        if not os.path.exists(dir_path):
            raise ValueError(f"Directory {dir_path} does not exist")

        query = f"{dir_path}/*.csv"
        # get just the csv file in the directory
        if files := glob(query):
            print(f"Loading {files[0]}")
            return pd.read_csv(files[0])
        return None

    def get_df_artist_lyrics_by_genius_id(self, artist_id: int) -> pd.DataFrame:

        # search with glob if there is a directory beginning with genius-{artist_id}
        if dirs := glob(f"{self.base_dir_path}/genius-{artist_id}-*"):
            # get the first one
            dir_path = dirs[0]
            return self._clean_df_lyrics(self._get_df_dataset_by_dirpath(dir_path))
        if len(dirs) == 0:
            raise ValueError(f"Artist with genius id {artist_id} not found")
        return None

    def get_df_artist_lyrics_by_name(self, artist_name: str) -> pd.DataFrame:

        artist_name = re.sub('[^A-Za-z0-9é]+', '', artist_name.lower())
        if dirs := glob(f"{self.base_dir_path}/genius-*-{artist_name}"):
            # get the first one
            dir_path = dirs[0]
            return self._clean_df_lyrics(self._get_df_dataset_by_dirpath(dir_path))
        if len(dirs) == 0:
            raise ValueError(f"Artist with name {artist_name} not found")
        return None

    def get_fr_en_artists(self, df_corpus: pd.DataFrame) -> list:
        if not {"language", "artist"}.issubset(df_corpus.columns):
            raise ValueError("Columns are not correct in the dataframe")

        df_corpus_group_lang = df_corpus.groupby("artist").agg({'language': lambda x: ' '.join(x)})

        df_corpus_group_lang["language"] = df_corpus_group_lang["language"].apply(lambda x: str(x).strip().split())
        df_corpus_group_lang["fr_songs"] = df_corpus_group_lang["language"].apply(lambda x: x.count("fr"))
        df_corpus_group_lang["en_songs"] = df_corpus_group_lang["language"].apply(lambda x: x.count("en"))
        df_corpus_group_lang["is_en"] = df_corpus_group_lang.apply(lambda x: int(x.fr_songs <= x.en_songs), axis=1)

        artists_en = df_corpus_group_lang[df_corpus_group_lang["is_en"] == 1].index.tolist()
        artists_fr = df_corpus_group_lang[df_corpus_group_lang["is_en"] == 0].index.tolist()
        return artists_fr, artists_en

    def get_full_df_lyrics_corpus(self, limit_nb_artists=None, only_french_artist=True,
                                  only_french_songs=True) -> pd.DataFrame:
        # dir exists
        if not os.path.exists(self.base_dir_path):
            raise ValueError(f"Directory {self.base_dir_path} does not exist")
        if files := glob(f"{self.base_dir_path}/*/*.csv"):

            files_filtered = files[:limit_nb_artists] if limit_nb_artists else files
            print(f"Loading {len(files_filtered)} csv files")
            df_corpus = pd.concat([pd.read_csv(file_path) for file_path in files_filtered], ignore_index=True)
            df_corpus = self._clean_df_lyrics(df_corpus)

            if only_french_artist:
                artists_fr, artists_en = self.get_fr_en_artists(df_corpus)
                self.artists_en = artists_en
                self.artists_fr = artists_fr
                df_corpus = df_corpus[df_corpus["artist"].isin(artists_fr)]

            if only_french_songs:
                df_corpus = df_corpus[df_corpus["language"] == "fr"]
            return df_corpus
        return None

    @staticmethod
    def lyrics_series_to_string(lyrics_series: pd.Series) -> str:
        return " ".join(lyrics_series.tolist())


if __name__ == "__main__":
    cdm = CorpusDataManager(columns_we_need=[])
    df1 = cdm.get_df_artist_lyrics_by_genius_id(1261)
    x = cdm.get_full_df_lyrics_corpus()
    df2 = cdm.get_df_artist_lyrics_by_name("rohff")
    print("artists_ids_names", cdm.artists_ids_names)
