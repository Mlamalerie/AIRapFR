from functools import partial
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from data.load import load_df_dataset
from data.preprocessing import preprocess_genius_text, tokens_2_str
from data.utils import display_loading

# %%
df_artist = load_df_dataset("data/datasets/genius-1908-rohff")
df_artist.head()
# %%

# get one lyrics test
lyrics = df_artist.iloc[0].lyrics
print(lyrics)


# %%
class DummyLyricsGenerator():
    """Class to generate lyrics with stupid way"""

    def __init__(self):
        self.words: list = []

    def train(self, df: pd.DataFrame):
        # check if column lyrics exists
        if "lyrics" not in df.columns:
            raise ValueError("Column lyrics not in the dataframe")

        preprocess = partial(preprocess_genius_text, token_output=True)
        series_lyrics_tokens = df["lyrics"].apply(preprocess).explode()
        self.words = series_lyrics_tokens.tolist()
        self.series_lyrics_tokens = series_lyrics_tokens

    def generate(self, starting_sent: str = "", max_len: int = 250) -> str:
        """Generate a lyrics with a starting sentence"""
        if len(self.words) == 0:
            raise ValueError("No words in the generator")

        return starting_sent + tokens_2_str(np.random.choice(self.words, max_len))


model = DummyLyricsGenerator()
model.train(df_artist)

# %%
print(model.generate("Je suis", max_len=250))
