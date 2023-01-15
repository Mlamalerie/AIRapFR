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

class MarkovChainLyricsGenerator():
    def __init__(self):
        self.table_proba = None
        self.k: int = Optional[int]

    def __freq_2_prob(self, table: dict) -> dict:
        for kx in table:
            s = float(sum(table[kx].values()))
            for k in table[kx].keys():
                table[kx][k] = table[kx][k] / s
        return table

    def __generate_table_from_one_lyrics(self, text: str, k: int, add_lower_k=True, init_table=None):
        if init_table is None:
            init_table = {}
        text_tokens = preprocess_genius_text(text, token_output=True)
        table = init_table
        for decrease_k in range(k if add_lower_k else 1):
            kk = k - decrease_k
            for i in range(len(text_tokens) - kk):
                x: tuple = tuple(text_tokens[i:i + kk])  # k-gram
                y: str = text_tokens[i + kk]  # next char
                # print("X  %s and Y %s  "%(X,Y))

                if table.get(x) is None:
                    table[x] = {y: 1}
                elif table[x].get(y) is None:
                    table[x][y] = 1
                else:
                    table[x][y] += 1
        return table

    def train(self, df: pd.DataFrame, k: int, add_lower_k=True):

        # check if column lyrics exists
        if "lyrics" not in df.columns:
            raise ValueError("Column lyrics not in the dataframe")

        # for each lyrics
        table = {}
        for i, lyrics in enumerate(df.lyrics):
            display_loading("Generating Markov Chain Model", i, len(df))
            table = self.__generate_table_from_one_lyrics(lyrics, k=k, init_table=table, add_lower_k=add_lower_k)
        display_loading("Generating Markov Chain Model", len(df), len(df))

        self.table_proba = self.__freq_2_prob(table)
        self.k = k

    def get_next_char(self, k_gram: tuple, void="", verbose=False) -> Tuple[str, float]:
        """ Get the next char from a k-gram (tuple)"""
        # print("#",k_gram)
        len_k_gram = len(k_gram)

        if len_k_gram > self.k:
            raise ValueError(f"the k-gram is too long, it should be <= {self.k}")

        if len_k_gram == 0:
            return void, 0.0

        if (k_gram[-1],) not in self.table_proba:  # if the last char is not in the table, (because yes it can happen)
            print(f"Warning : {k_gram[-1]} not in the model")
            return void, 0.0  # i choose to return void

        if k_gram not in self.table_proba:
            return self.get_next_char(k_gram[1:])

        possible_chars = list(self.table_proba[k_gram].keys())
        possible_values = list(self.table_proba[k_gram].values())
        # print("###",possible_chars)
        next_char = np.random.choice(possible_chars, p=possible_values)
        return next_char, self.table_proba[k_gram][next_char]

    def generate(self, starting_sent, max_len=800):
        """ Generate a lyrics from a starting sentence"""
        # verif if starting_sent len is >= k
        tokenized_sentence = tuple(preprocess_genius_text(starting_sent, token_output=True))
        # verif the model is trained
        if self.table_proba is None:
            raise ValueError("Model not trained")
        for _ in range(max_len):
            x = tokenized_sentence[-self.k:]
            # print(x)
            next_char, next_char_proba = self.get_next_char(x)
            # print(x,next_char)
            tokenized_sentence += (next_char,)

        return tokens_2_str(tokenized_sentence)


# %%
model = MarkovChainLyricsGenerator()
model.train(df_artist, k=4)

# %%
starting_sent = "j'me suis fait"
x = tuple(preprocess_genius_text(starting_sent, token_output=True))
print(model.get_next_char(x))
# %%
print(model.generate("Je suis", max_len=250))

# todo : remove punctuation
