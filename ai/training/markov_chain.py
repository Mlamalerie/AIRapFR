from typing import Optional, Tuple

import numpy as np
import pandas as pd

from data.load import load_df_dataset
from data.preprocessing import preprocess_genius_text, tokens_2_str
from utils import display_loading


class MarkovChainLyricsGenerator():
    def __init__(self, is_stupid=False):
        self.table_proba = None
        self.k: int = Optional[int]
        self.name = "Markov Chain"
        self.is_stupid = is_stupid  # todo : rename

    def set_stupid(self, is_stupid):
        self.is_stupid = is_stupid

    def __freq_2_prob(self, table: dict) -> dict:
        for kx in table:
            s = float(sum(table[kx].values()))
            for k in table[kx].keys():
                table[kx][k] = table[kx][k] / s
        return table

    def __generate_table_from_one_lyrics(self, text: str, k: int, add_lower_k=True, init_table=None):
        if init_table is None:
            init_table = {}
        text_tokens = preprocess_genius_text(text, tokenised_output=True)  # todo : remove punctuation ?
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
            display_loading(f"Generating {self.name} Model", i, len(df))
            table = self.__generate_table_from_one_lyrics(lyrics, k=k, init_table=table, add_lower_k=add_lower_k)
        display_loading(f"Generating {self.name} Model", len(df), len(df))

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

        possible_chars = list(self.table_proba[k_gram].keys())  # get the possible chars
        possible_values = list(self.table_proba[k_gram].values())  # get the proba of each char
        # print("###",possible_chars)
        next_char = np.random.choice(possible_chars, p=possible_values if not self.is_stupid else None)
        return next_char, self.table_proba[k_gram][next_char]

    def generate(self, starting_sent, max_len=800):  # todo : add same_proba param
        """ Generate a lyrics from a starting sentence"""
        # todo : manage the case where the starting sentence is None
        # verif if starting_sent len is >= k
        tokenized_sentence = tuple(preprocess_genius_text(starting_sent, tokenised_output=True))
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
