import ast
from functools import partial
import os
import numpy as np
import pandas as pd
import random
from data.load_corpus import CorpusDataManager
from data.preprocessing import tokens_2_str
import pickle
from glob import glob


# %%
class DummyLyricsGenerator():
    """Class to generate lyrics with stupid way"""

    def __init__(self):
        self.words: list = []
        self.artists: list = []

    def train(self, df: pd.DataFrame):
        # check if column lyrics exists
        if "lyrics" not in df.columns:
            raise ValueError("Column lyrics not in the dataframe")

        # preprocess = partial(preprocess_genius_text, token_output=True)
        series_lyrics_tokens = df["lyrics"].explode()
        self.words = series_lyrics_tokens.unique().tolist()
        self.series_lyrics_tokens = series_lyrics_tokens

        # get artists unique list
        self.artists = df["primary_artist.id"].astype(str).unique().tolist()

    def generate_text(self, starting_sent: str = "", max_len: int = 250,return_with_starting_sent=True) -> str:
        """Generate a lyrics with a starting sentence"""
        if len(self.words) == 0:
            raise ValueError("No words in the generator")
        starting_sent_split = starting_sent.split(" ")
        generated_list = [random.choice(self.words) for _ in range(max_len - len(starting_sent_split))]
        return starting_sent + " " + tokens_2_str(generated_list) if return_with_starting_sent else tokens_2_str(generated_list)

    def save(self, dir_path: str):
        """Save the model (with pickle)"""
        # verify if dir_path exists
        if not os.path.exists(dir_path):
            raise ValueError(f"Path {dir_path} does not exist")
        path = os.path.join(dir_path,
                            f"dummy_model__{'_'.join(self.artists) if len(self.artists) == 1 else f'artists_{len(self.artists)}'}.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
            print(f"Model saved at {path}")

    @staticmethod
    def load(path: str):
        """Load the model (with pickle)"""
        # verify if path exists
        if not os.path.exists(path):
            raise ValueError(f"Path {path} does not exist")
        with open(path, "rb") as f:
            return pickle.load(f)

def load_dummy_model_from_disk(cdm : CorpusDataManager, artist_name = None) -> DummyLyricsGenerator:
    """Load a dummy model from disk"""
    abs_path = os.path.dirname(os.path.abspath(__file__))
    if artist_name is None:

        query = f"{abs_path}/models/dummy/dummy_model__artists*.pkl"
        if found_paths := glob(query):
            path = found_paths[0]
            return DummyLyricsGenerator.load(path)
        else:
            raise ValueError(f"No dummy model found for multiple artists")
    else:
        artist_id = cdm.get_id_from_artist_name(artist_name)
        query = f"{abs_path}/models/dummy/dummy_model__{artist_id}.pkl"
        if found_paths := glob(query):
            path = found_paths[0]
            return DummyLyricsGenerator.load(path)
        else:
            raise ValueError(f"No dummy model found for artist_name={artist_name}")

def main() -> None:
    cdm = CorpusDataManager()
    artist_name = "rohff"

    df_artist = cdm.get_df_lyrics_preprocessed_by_name(artist_name, punct_removal=True, tokenised_output=True)
    df_artist["lyrics"] = df_artist["lyrics"].progress_apply(ast.literal_eval)

    model = DummyLyricsGenerator()
    model.train(df_artist)

    model.save("models/dummy")

    generated_text = model.generate_text("Je suis", max_len=50)
    print(generated_text)




if __name__ == "__main__":
    main()
