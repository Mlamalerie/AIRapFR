import os
import re
from glob import glob
from typing import Tuple
from tqdm import tqdm
import numpy as np
import pandas as pd

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


class CorpusDataManager():
    def __init__(self, base_dir_path=f"{ROOT_PATH}/corpus", columns_we_need=None, verbose = False):

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
        self.verbose = verbose
        self.base_dir_path = base_dir_path
        self.columns_we_need = columns_we_need
        self.available_artists_ids_names, self.available_artists_ids_paths = self.get_available_artists()
        self.available_artists_names_ids = {v: k for k, v in self.available_artists_ids_names.items()}
        self.available_artists_names_paths = {v: k for k, v in self.available_artists_ids_paths.items()}

    def get_available_artists(self) -> Tuple[dict, dict]:
        if dirs := glob(f"{self.base_dir_path}/*"):
            return {
                int(os.path.basename(dir_path)
                .split("-")[1]): os.path.basename(dir_path)
                .split("-")[-1]
                for dir_path in dirs
            }, {
                int(os.path.basename(dir_path)
                .split("-")[1]): dir_path
                for dir_path in dirs
            }
        return None, None

    def get_id_by_artist_name(self, artist_name: str) -> int:
        artist_name = re.sub('[^A-Za-z0-9é]+', '', artist_name.lower())
        if artist_name in self.available_artists_names_ids:
            return self.available_artists_names_ids[artist_name]
        return None

    def get_artist_name_by_id(self, artist_id: int) -> str:
        if artist_id in self.available_artists_ids_names:
            return self.available_artists_ids_names[artist_id]
        return None

    def _clean_df_lyrics(self, df):
        if df is None:
            return None
        # raise error if df don't have the right columns
        if not {"artist", "lyrics"}.issubset(df.columns):  # todo : add 'primary_artist.id'
            raise ValueError("Columns are not correct in the dataframe")

        # remove empty lyrics
        df = df.dropna(subset=['lyrics'])

        # remove duplicates
        df = df.drop_duplicates(subset=['lyrics'])

        # manage type
        df['lyrics'] = df['lyrics'].astype(str)
        df['artist'] = df['artist'].astype(str)

        for col in ["language", "title", "album.name", "artist_names"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
            elif col in self.columns_we_need:  # if we need it but it's not in the df
                self.columns_we_need.remove(col)

        # int dtype={'id': 'Int64'} date, datetime ect

        # select columns we need
        if self.columns_we_need:
            df = df[self.columns_we_need].reset_index(drop=True)

        df = df.sort_values(
            by=[col for col in ['primary_artist.id', 'album.name', 'release_date_components.year', 'title'] if
                col in df.columns]).reset_index(drop=True)

        if "release_date_components.year" in df.columns:
            df["release_date_components.year"] = df["release_date_components.year"].where(
                df["release_date_components.year"] >= 1800, np.nan)

            # Remplacer les valeurs NaN de la colonne "year" par la valeur de la même colonne du même artiste
            df["release_date_components.year"] = df["release_date_components.year"].fillna(method="ffill", limit=1)

        return df

    def _get_df_dataset_by_dirpath(self, dir_path: str) -> pd.DataFrame:
        # dir exists
        if not os.path.exists(dir_path):
            raise ValueError(f"Directory {dir_path} does not exist")

        query = f"{dir_path}/df_genius_*.csv"
        # get just the csv file in the directory
        if files := glob(query):
            # loading basename
            if self.verbose:
                print(f"Loading {os.path.basename(files[0])}")
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

    def _get_df_lyrics_preprocessed_by_dirpath(self, dir_path: str, lemmatization=False,
                                               stop_words_removal=False, punct_removal=False, tokenised_output=True,
                                               crop_first_lines=True) -> pd.DataFrame:
        # dir exists
        if not os.path.exists(dir_path):
            raise ValueError(f"Directory {dir_path} does not exist")

        query = f"{dir_path}/df_lyrics_preprocessed_"
        if tokenised_output:
            query += "tok_"
        if lemmatization:
            query += "lemma_"
        if stop_words_removal:
            query += "rmstop_"
        if punct_removal:
            query += "rmpunct_"
        if crop_first_lines:
            query += "crop_"

        query += ".csv"

        if not os.path.exists(query):
            return None

        # get just the csv file in the directory
        if files := glob(query):
            # loading basename
            if self.verbose:
                print(f"Loading {os.path.basename(files[0])}")
            return pd.read_csv(files[0])

    def get_df_lyrics_preprocessed_by_genius_id(self, artist_id: int, lemmatization=False,
                                                stop_words_removal=False, punct_removal=False, tokenised_output=True,
                                                crop_first_lines=True) -> pd.DataFrame:

        # search with glob if there is a directory beginning with genius-{artist_id}
        if dirs := glob(f"{self.base_dir_path}/genius-{artist_id}-*"):
            # get the first one
            dir_path = dirs[0]
            return self._get_df_lyrics_preprocessed_by_dirpath(dir_path, lemmatization, stop_words_removal,
                                                               punct_removal, tokenised_output, crop_first_lines)
        if len(dirs) == 0:
            raise ValueError(f"Artist with genius id {artist_id} not found")
        return None

    def get_df_lyrics_preprocessed_by_name(self, artist_name: str, lemmatization=False,
                                           stop_words_removal=False, punct_removal=False, tokenised_output=True,
                                           crop_first_lines=True) -> pd.DataFrame:

        artist_name = re.sub('[^A-Za-z0-9é]+', '', artist_name.lower())
        if dirs := glob(f"{self.base_dir_path}/genius-*-{artist_name}"):
            # get the first one
            dir_path = dirs[0]
            return self._get_df_lyrics_preprocessed_by_dirpath(dir_path, lemmatization, stop_words_removal,
                                                               punct_removal, tokenised_output, crop_first_lines)
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
                                  only_french_songs=True, preprocessed=False,
                                  ignore_artist_ids: list = None, punct_removal=False, tokenised_output=True,crop_first_lines=True) -> pd.DataFrame:
        # dir exists
        if not os.path.exists(self.base_dir_path):
            raise ValueError(f"Directory {self.base_dir_path} does not exist")

        csv_query = f"{self.base_dir_path}/*/"

        if not preprocessed:
            csv_query_name = "df_genius_*"
        else:
            csv_query_name = "df_lyrics_preprocessed_"
            if tokenised_output:
                csv_query_name += "tok_"
            if punct_removal:
                csv_query_name += "rmpunct_"
            if crop_first_lines:
                csv_query_name += "crop_"

        csv_query += f"{csv_query_name}.csv"

        if files := glob(csv_query):
            files_filtered = files[:limit_nb_artists] if limit_nb_artists else files

            print(f"Loading {len(files_filtered)} csv files")
            df_corpus = pd.concat([pd.read_csv(file_path) for file_path in tqdm(files_filtered)], ignore_index=True)
            df_corpus = self._clean_df_lyrics(df_corpus)

            if only_french_artist:
                artists_fr, artists_en = self.get_fr_en_artists(df_corpus)
                self.artists_en = artists_en
                self.artists_fr = artists_fr
                df_corpus = df_corpus[df_corpus["artist"].isin(artists_fr)].reset_index(drop=True)

            if ignore_artist_ids is not None and len(ignore_artist_ids) > 0:
                df_corpus = df_corpus[~df_corpus["primary_artist.id"].isin(ignore_artist_ids)].reset_index(drop=True)

            if only_french_songs:
                df_corpus = df_corpus[df_corpus["language"] == "fr"].reset_index(drop=True)
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
