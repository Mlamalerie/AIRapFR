import pickle
import numpy as np
import ast
import pandas as pd
from data.load_corpus import CorpusDataManager
import argparse
import os
from tqdm import tqdm
from utils import create_dir
from datetime import datetime
from glob import glob

# Parameters -----------------
PREPROCESSING_PUNCT_REMOVAL = True
PREPROCESSING_TOKENISED_OUTPUT = True
MAX_YEAR_FILTER = 2015

BOOL_IGNORE_WORD = True
MIN_WORD_FREQUENCY = 6
MAX_SENTENCE_LENGTH = 10
STEP = 1

PERCENTAGE_TEST = 0.1

ARTIST_NAME_FOCUS = "kery james"

# ----------------------------
DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + "/datasets"


def get_tokens_from_preprocessed_df(df_corpus: pd.DataFrame, min_word_frequency=2, bool_ignore_word=True) -> None:
    if isinstance(df_corpus["lyrics"][0], str):
        print("formatting lyrics column to list...", end=" ")
        df_corpus["lyrics"] = df_corpus["lyrics"].progress_apply(ast.literal_eval)

    df_lyrics_explode = df_corpus["lyrics"].explode()
    corpus_tokens = df_lyrics_explode.tolist()

    print(
        'Corpus length in characters:',
        sum(len(token) for token in corpus_tokens),
    )
    print('Corpus length in words:', len(corpus_tokens))

    set_words = set(corpus_tokens)
    print('Unique words before ignoring:', len(set_words))
    ignored_set_words = set()
    table_tokens_value_counts = df_lyrics_explode.value_counts()
    print(f"Mean {table_tokens_value_counts.mean()} - Median {table_tokens_value_counts.median()} - Q(0.25) {table_tokens_value_counts.quantile(0.25)} - Q(0.75) {table_tokens_value_counts.quantile(0.75)}")

    if bool_ignore_word:
        ignored_set_words = set(
            table_tokens_value_counts[table_tokens_value_counts < min_word_frequency].index.tolist())

        print('Ignoring words with frequency <', min_word_frequency)
        # new set of words without ignored words
        set_words = set_words - ignored_set_words
        print('Unique words after ignoring:', len(set_words))

    # display head of table and tail of table (to dict)
    print("Head of table:")
    table_tokens_value_counts_filtered = table_tokens_value_counts[table_tokens_value_counts >= min_word_frequency]
    print(table_tokens_value_counts_filtered.head(10).to_dict())
    print("Tail of table:")
    print(table_tokens_value_counts_filtered.tail(10).to_dict())
    print(f"Mean {table_tokens_value_counts_filtered.mean()} - Median {table_tokens_value_counts_filtered.median()} - Q(0.25) {table_tokens_value_counts_filtered.quantile(0.25)} - Q(0.75) {table_tokens_value_counts_filtered.quantile(0.75)}")

    return corpus_tokens, set_words, ignored_set_words


def generate_sentences_next_words_dataset(corpus_tokens, ignored_set_words=set(), max_sentence_length=10,
                                          step=1) -> None:
    # generate sentences & next word
    sentences = []
    next_words = []
    ignored = 0

    for i in range(0, len(corpus_tokens) - max_sentence_length, step):
        sentence = corpus_tokens[i: i + max_sentence_length]
        next_word = corpus_tokens[i + max_sentence_length]

        # Only add sequences where no word is in ignored_words
        if len(set(sentence + [next_word]).intersection(ignored_set_words)) == 0:
            sentences.append(sentence)
            next_words.append(next_word)
        else:
            ignored = ignored + 1

    print('Ignored sequences:', ignored)
    print('Number of sentences:', len(sentences))
    print('Number of next words:', len(next_words))

    return sentences, next_words


def split_training_and_test_set(sentences_original, next_original, percentage_test=0.1, seed=123):
    # shuffle the data in unison
    np.random.seed(seed)
    shuffled_indices = np.random.permutation(len(sentences_original))
    sentences_shuffled = [sentences_original[i] for i in shuffled_indices]
    next_words_shuffled = [next_original[i] for i in shuffled_indices]

    # split the data into training and test sets
    cut_index = int(len(sentences_original) * percentage_test)
    x_test, x_train = sentences_shuffled[:cut_index], sentences_shuffled[cut_index:]
    y_test, y_train = next_words_shuffled[:cut_index], next_words_shuffled[cut_index:]

    print("Size of training set = %d" % len(x_train))
    print("Size of test set = %d" % len(y_test))
    return (x_train, y_train), (x_test, y_test)


def get_word_index_dict(set_words):
    word_index_dict = {c: i+1 for i, c in enumerate(set_words)}
    index_word_dict = dict(enumerate(set_words))
    return word_index_dict, index_word_dict


def generate_dataset_from_corpus(df_corpus: pd.DataFrame, max_year_filter: int = None, bool_ignore_word=True,
                                 min_word_frequency=2,
                                 max_sentence_length=10, step=1, percentage_test=0.1) -> None:
    params_str = f"min_freq_{min_word_frequency if bool_ignore_word else 0}__sent_len_{max_sentence_length}__step_{step}__p_test_{percentage_test}"

    # filter rap corpus by year
    if max_year_filter is not None:
        df_corpus = df_corpus[df_corpus["release_date_components.year"] <= max_year_filter].reset_index(drop=True)
        params_str += f"__max_year_{max_year_filter}"

    # generate rap corpus dataset sentences & next word
    corpus_tokens, set_words, ignored_set_words = get_tokens_from_preprocessed_df(df_corpus,
                                                                                  min_word_frequency=min_word_frequency,
                                                                                  bool_ignore_word=bool_ignore_word)

    # generate sentences & next word
    sentences, next_words = generate_sentences_next_words_dataset(corpus_tokens, ignored_set_words=ignored_set_words,
                                                                  max_sentence_length=max_sentence_length, step=step)

    # get word index dict
    word_index_dict, index_word_dict = get_word_index_dict(set_words)

    # split training and test set
    (sentences_train, next_words_train), (sentences_test, next_words_test) = split_training_and_test_set(sentences,
                                                                                                         next_words,
                                                                                                         percentage_test=percentage_test)
    len_dataset = len(sentences)
    return sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict, index_word_dict, len_dataset, params_str


def save_dataset_with_pickle(dir_path, name, sentences_train, next_words_train, sentences_test, next_words_test,
                             set_words, word_index_dict, index_word_dict, len_dataset, params_str):
    file_path = os.path.join(dir_path, name + "__" + params_str + ".pkl")
    # save dataset with pickle
    with open(file_path, 'wb') as f:
        pickle.dump((sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict,
                     index_word_dict, len_dataset), f)
    return file_path



def main() -> None:
    tqdm.pandas()
    global PREPROCESSING_PUNCT_REMOVAL, PREPROCESSING_TOKENISED_OUTPUT
    global ARTIST_NAME_FOCUS, MAX_YEAR_FILTER, MIN_WORD_FREQUENCY, MAX_SENTENCE_LENGTH, PERCENTAGE_TEST, BOOL_IGNORE_WORD, STEP

    # 1.1. load 1 rap corpus (with all french artist)
    print(">>>>>> 1.1. Loading rap corpus...")
    corpus_mng = CorpusDataManager()
    artist_id = None
    if ARTIST_NAME_FOCUS is not None:
        artist_id = corpus_mng.get_id_from_artist_name(ARTIST_NAME_FOCUS)

    df_rap_fr_corpus = corpus_mng.get_full_df_lyrics_corpus(preprocessed=True,
                                                            only_french_artist=True,
                                                            punct_removal=PREPROCESSING_PUNCT_REMOVAL,
                                                            tokenised_output=PREPROCESSING_TOKENISED_OUTPUT,
                                                            ignore_artist_ids=[
                                                                artist_id] if artist_id and ARTIST_NAME_FOCUS else None)
    if df_rap_fr_corpus is None:
        raise Exception("df_rap_fr_corpus is None")

    rap_fr_corpus_params_str = str(len(df_rap_fr_corpus)) + "__"
    if PREPROCESSING_TOKENISED_OUTPUT:
        rap_fr_corpus_params_str += "tok_"
    if PREPROCESSING_PUNCT_REMOVAL:
        rap_fr_corpus_params_str += "rmpunct_"

    # 1.2. generate rap corpus dataset sentences & next word
    print(">>>>>> 1.2. Generating rap corpus dataset sentences & next word...")
    sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict, index_word_dict, len_dataset, params_str = generate_dataset_from_corpus(
        df_rap_fr_corpus, max_year_filter=MAX_YEAR_FILTER, bool_ignore_word=BOOL_IGNORE_WORD,
        min_word_frequency=MIN_WORD_FREQUENCY, max_sentence_length=MAX_SENTENCE_LENGTH, percentage_test=PERCENTAGE_TEST)

    # 1.3. save dataset with pickle
    print(">>>>>> 1.3. Saving dataset with pickle...")

    # get now datetime format YYYYMMDD
    now_str = datetime.now().strftime("%Y%m%d")
    dataset_name = f"dataset"
    if artist_id:
        dataset_name += f"-{artist_id}-{corpus_mng.get_artist_name_by_id(artist_id)}"
    dataset_name += f"-{now_str}"

    file_path = save_dataset_with_pickle(dir_path=create_dir(DIR_PATH, dataset_name), name="rap_corpus",
                                         sentences_train=sentences_train,
                                         next_words_train=next_words_train, sentences_test=sentences_test,
                                         next_words_test=next_words_test, set_words=set_words,
                                         word_index_dict=word_index_dict,
                                         index_word_dict=index_word_dict, len_dataset=len_dataset,
                                         params_str=f"{rap_fr_corpus_params_str}_{params_str}")
    print(f"Dataset saved with pickle at : {file_path}")

    if not artist_id:
        return

    # 2.1. load 1 rap corpus (with only artist focus)
    print(f">>>>>> 2.1. Loading {ARTIST_NAME_FOCUS} corpus...")
    df_corpus = corpus_mng.get_df_lyrics_preprocessed_by_genius_id(artist_id, punct_removal=PREPROCESSING_PUNCT_REMOVAL,
                                                                   tokenised_output=PREPROCESSING_TOKENISED_OUTPUT)
    if df_corpus is None:
        raise Exception("df_corpus is None")
    corpus_params_str = str(len(df_corpus)) + "__"
    if PREPROCESSING_TOKENISED_OUTPUT:
        corpus_params_str += "tok_"
    if PREPROCESSING_PUNCT_REMOVAL:
        corpus_params_str += "rmpunct_"

    # 2.2. generate rap corpus dataset sentences & next word
    print(f">>>>>> 2.2. Generating {ARTIST_NAME_FOCUS} corpus dataset sentences & next word...")
    sentences_train_artist, next_words_train_artist, sentences_test_artist, next_words_test_artist, set_words_artist, word_index_dict_artist, index_word_dict_artist, len_dataset_artist, params_str_artist = generate_dataset_from_corpus(
        df_corpus, max_year_filter=MAX_YEAR_FILTER, bool_ignore_word=False,
        min_word_frequency=MIN_WORD_FREQUENCY, max_sentence_length=MAX_SENTENCE_LENGTH, percentage_test=PERCENTAGE_TEST)

    # 2.3. save dataset with pickle
    print(f">>>>>> 2.3. Saving {ARTIST_NAME_FOCUS} dataset with pickle...")
    file_path = save_dataset_with_pickle(dir_path=create_dir(DIR_PATH, dataset_name),
                                         name=corpus_mng.get_artist_name_by_id(artist_id),
                                         sentences_train=sentences_train_artist,
                                         next_words_train=next_words_train_artist, sentences_test=sentences_test_artist,
                                         next_words_test=next_words_test_artist, set_words=set_words_artist,
                                         word_index_dict=word_index_dict_artist, index_word_dict=index_word_dict_artist,
                                         len_dataset=len_dataset_artist,
                                         params_str=f"{corpus_params_str}_{params_str_artist}")
    print(f"Dataset saved with pickle at : {file_path}")

    # 3.1 Fuse sets
    print(f">>>>>> 3. Fusing sets...")
    set_words_union = set_words.union(set_words_artist)
    word_index_dict_union = {word: index for index, word in enumerate(set_words_union)}
    print(f"set_words_union : {len(set_words_union)}")
    # 3.2 save word_index_dict_union object with pickle
    pickle.dump(word_index_dict_union,
                open(os.path.join(create_dir(DIR_PATH, dataset_name), "word_index_dict_union.pkl"), "wb"))


if __name__ == "__main__":
    main()
