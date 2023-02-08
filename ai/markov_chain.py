from typing import Optional, Tuple
from glob import glob
import numpy as np
import random
import pandas as pd
import ast
import os
import pickle

from data.load_corpus import CorpusDataManager
from data.preprocessing import preprocess_genius_text, tokens_2_str

from tqdm import tqdm



class MarkovChainLyricsGenerator():
    def __init__(self, is_stupid=False):
        self.table_proba = None
        self.min_freq = None
        self.k: int = Optional[int]
        self.is_stupid = is_stupid  # todo : rename
        self.artists: list = []

    def set_stupid(self, is_stupid):
        self.is_stupid = is_stupid

    def __freq_2_prob(self, table: dict) -> dict:
        for kx in table:
            s = float(sum(table[kx].values()))
            for k in table[kx].keys():
                table[kx][k] = table[kx][k] / s
        return table

    def __generate_table_from_one_lyrics(self, text_tokens: str, k: int, add_lower_k=True, init_table=None):
        if init_table is None:
            init_table = {}
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

    def train(self, df: pd.DataFrame, k: int, add_lower_k=True, min_freq=0):

        # check if column lyrics exists
        if "lyrics" not in df.columns:
            raise ValueError("Column lyrics not in the dataframe")

        # get artists unique list
        self.artists = df["primary_artist.id"].astype(str).unique().tolist()
        self.min_freq = min_freq

        # for each lyrics
        table = {}
        for lyrics_tokens in tqdm(df.lyrics, desc=f"Generating Markov Chain Model [k={k}] ({'_'.join(self.artists) if len(self.artists) < 5 else f'len_artists={len(self.artists)}'}) "):
            table = self.__generate_table_from_one_lyrics(lyrics_tokens, k=k, init_table=table, add_lower_k=add_lower_k)

        # remove low freq
        if min_freq > 1:
            for kx in list(table.keys()):
                for ky in list(table[kx].keys()):
                    if table[kx][ky] < min_freq:
                        del table[kx][ky]
                if len(table[kx]) == 0:
                    del table[kx]
        self.table_proba = self.__freq_2_prob(table)
        self.k = k


    def get_next_char(self, k_gram: tuple, null="", verbose=False) -> Tuple[str, float]:
        """ Get the next char from a k-gram (tuple)"""
        # print("#",k_gram)
        len_k_gram = len(k_gram)

        if len_k_gram > self.k:
            raise ValueError(f"the k-gram is too long, it should be <= {self.k}")

        if len_k_gram == 0:
            return null, 0.0

        if (k_gram[-1],) not in self.table_proba:  # if the last char is not in the table, (because yes it can happen)
            if verbose:
                print(f"Warning : '{k_gram[-1]}' not in the model")
            return null, 0.0  # i choose to return void

        if k_gram not in self.table_proba:
            if verbose:
                print(f"Warning : '{k_gram}' not in the model")
            return self.get_next_char(k_gram[1:])

        possible_chars = list(self.table_proba[k_gram].keys())  # get the possible chars
        possible_values = list(self.table_proba[k_gram].values())  # get the proba of each char
        # print("###",possible_chars)
        next_char = np.random.choice(possible_chars, p=possible_values if not self.is_stupid else None)
        return next_char, self.table_proba[k_gram][next_char]

    def generate_text(self, starting_sent, max_len=800, return_with_starting_sent=True):  # todo : add same_proba param
        """ Generate a lyrics from a starting sentence"""
        #print("Generating lyrics from starting sentence : ", starting_sent)
        # verif the model is trained
        if self.table_proba is None or len(self.table_proba) == 0:
            raise ValueError("Model not trained")
        #print(len(starting_sent),"~~")
        if starting_sent is None or len(starting_sent) == 0:
            # choose a random starting sentence (one of the k-gram)
            tokenized_sentence = random.choice(list(self.table_proba.keys()))

        else:
            # verif if starting_sent len is >= k
            tokenized_sentence = tuple(
                preprocess_genius_text(starting_sent, tokenised_output=True))
            len_starting_tokenized_sentence = len(tokenized_sentence)

        #print("Starting sentence : ", tokenized_sentence)
        for _ in range(max_len):
            x = tokenized_sentence[-self.k:]
            # print(x)
            #print(f"Current k-gram : {x}")
            next_char, next_char_proba = self.get_next_char(x)
            # print(x,next_char)
            tokenized_sentence += (next_char,)

            #print(f"Next char : {next_char} (proba : {next_char_proba}) ; tokenized sentence : {tokenized_sentence}")

        #print(len_starting_tokenized_sentence,"~~", tokens_2_str(tokenized_sentence) if return_with_starting_sent else tokens_2_str(tokenized_sentence[len_starting_tokenized_sentence:]))
        return tokens_2_str(tokenized_sentence) if return_with_starting_sent else tokens_2_str(tokenized_sentence[len_starting_tokenized_sentence:])

    def get_adj_matrix(self):
        self.adj_matrix = np.zeros((len(self.table_proba), len(self.table_proba)))

    def save(self, dir_path: str):
        """Save the model (with pickle)"""
        if self.table_proba is None or len(self.table_proba) == 0:
            raise ValueError("Model not trained")
        # verify if dir_path exists
        if not os.path.exists(dir_path):
            raise ValueError(f"Path {dir_path} does not exist")
        path = os.path.join(dir_path,
                            f"markov_chain_model__{'_'.join(self.artists) if len(self.artists) == 1 else f'artists_{len(self.artists)}'}__k_{self.k}__min_freq_{self.min_freq}.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
            print(f"> Model saved at {path}")

    @staticmethod
    def load(path: str):
        """Load the model (with pickle)"""
        # verify if path exists
        if not os.path.exists(path):
            raise ValueError(f"Path {path} does not exist")
        with open(path, "rb") as f:
            print(f"> Model loaded from {path}")
            return pickle.load(f)


def main() -> None:
    """Main function"""
    cdm = CorpusDataManager()
    artist_name = "Booba"
    min_freq = 0
    multiple_artist, limit = False, None


    # get the data

    if multiple_artist:
        df = cdm.get_full_df_lyrics_corpus(preprocessed=True, punct_removal=True, tokenised_output=True, limit_nb_artists=limit)
    else:
        df = cdm.get_df_lyrics_preprocessed_by_name(artist_name, punct_removal=True, tokenised_output=True)
    df["lyrics"] = df["lyrics"].progress_apply(ast.literal_eval)


    for k in range(1, 7):
        # get the model
        mc_model = MarkovChainLyricsGenerator()

        # train the model
        mc_model.train(df, k=k, min_freq=min_freq)

        # save the model
        mc_model.save("models/markov_chain")

        # generate a lyrics
        print(f"===================================== k={k}")
        print(mc_model.generate_text("", max_len=50))

def load_markov_model_from_disk(cdm : CorpusDataManager,k = 2, min_freq = 0, artist_name = None) -> MarkovChainLyricsGenerator:
    """Load a markov model from disk"""
    abs_path = os.path.abspath(os.path.dirname(__file__))
    if artist_name is None:
        # example : markov_chain_model__artists_430__k_1__min_freq_2.pkl
        query = f"{abs_path}/models/markov_chain/markov_*model__artists_*__k_{k}__min_freq_{min_freq}.pkl"
        if found_paths := glob(query):
            path = found_paths[0]
            return MarkovChainLyricsGenerator.load(path)
        else:
            raise ValueError(f"No markovchain model found for k={k}, min_freq={min_freq} and multiple artists")
    else:
        artist_id = cdm.get_id_from_artist_name(artist_name)
        # example : markov_chain_model__1273__k_1__min_freq_0.pkl
        query = f"{abs_path}/models/markov_chain/markov_*model__{artist_id}__k_{k}__min_freq_{min_freq}.pkl"
        if found_paths := glob(query):
            path = found_paths[0]
            return MarkovChainLyricsGenerator.load(path)
        else:
            raise ValueError(f"No markovchain model found for k={k}, artist_name={artist_name}, min_freq={min_freq}")




if __name__ == "__main__":
    main()
    #mc = load_markov_model_from_disk(CorpusDataManager(),k = 2, min_freq = 2, artist_name = "kery james")
    #print(mc.generate_text("je suis", max_len=50))
