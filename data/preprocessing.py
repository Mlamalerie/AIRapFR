import os
import re
from functools import partial
from data.load_corpus import CorpusDataManager
import spacy
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
# from pandarallel import pandarallel
from glob import glob
# pandarallel.initialize()
from tqdm import tqdm

tqdm.pandas()
nlp = spacy.load("fr_core_news_sm")
# nlp.Defaults.stop_words.add("my_new_stopword")
# print(nlp.Defaults.stop_words)

cdm = CorpusDataManager()


# %%


def remove_section_brackets(text):
    return re.sub(r"(\[.*?\] \(.*?\))|(\[(.+)\])", "", text)  # avant ça split coulot refrain prendre en compte


def slice_lines(text, deb=None, fin=None):
    text = "\n".join(text.split("\n")[deb:fin])
    return text


def tokens_2_str(tokens: list) -> str:
    return " ".join(tokens).strip().replace("' ", "'").replace(" - ", "-").replace(" ,", ",").replace("\n ", "\n")


# main function to preprocess text, with parameters to choose which preprocessing steps to apply
def preprocess_genius_text(text, lower_case=True, lemmatization=False, stop_words_removal=False,
                           stop_words_to_keep=None, punct_removal=False, tokenised_output=False, crop_first_lines=True):
    if stop_words_to_keep is None:
        stop_words_to_keep = []
    # Exclude section brackets
    text = remove_section_brackets(text)
    if crop_first_lines and len(text.split("\n")) > 10:
        text = slice_lines(text, deb=1)
    text = text.strip()
    # lower case
    if lower_case:
        text = text.lower()
    # remove extra whitespace
    text = text.replace(u'\xa0', u' ')
    text = re.sub('[ ]+', ' ', text)
    text = re.sub('[\n]+', '\n', text)
    text = re.sub('\n ', '\n', text)
    tokens = list(nlp(text))

    # todo : manage contractions (j' => je, c' => ce, etc.)

    # stop words removal from tokenized text
    if stop_words_removal:
        tokens = [token for token in tokens if not token.is_stop or token.text in stop_words_to_keep]

    # punctuation removal
    if punct_removal:
        tokens = [token for token in tokens if not token.is_punct]

    # lemmatization from tokens
    if lemmatization:
        tokens = [token.lemma_ for token in tokens]
    else:
        tokens = [token.text for token in tokens]
    return tokens if tokenised_output else tokens_2_str(tokens)


# %%
def preprocess_genius_lyrics_from_df(df, lemmatization=False, stop_words_removal=False,
                                     stop_words_to_keep=None, punct_removal=False, tokenised_output=False,
                                     crop_first_lines=True, overwrite_lyrics_column=False):
    df = df.copy()
    if stop_words_to_keep is None:
        stop_words_to_keep = ["je", "tu", "il", "elle", "nous", "vous", "être", "avoir"]
    f_preprocessing = partial(preprocess_genius_text, lower_case=True, lemmatization=lemmatization,
                              stop_words_removal=stop_words_removal, stop_words_to_keep=stop_words_to_keep,
                              punct_removal=punct_removal, tokenised_output=tokenised_output,
                              crop_first_lines=crop_first_lines)
    column_name = "lyrics" if overwrite_lyrics_column else "lyrics_preprocessed"
    # df[column_name] = df['lyrics'].progress_apply(f_preprocessing)
    df[column_name] = df['lyrics'].apply(f_preprocessing)
    # df["lyrics_preprocessed"] = df['lyrics'].parallel_apply(f_preprocessing)

    return df


# new_df = preprocess_genius_lyrics_from_df(df)

# %%

def get_str_preprocess_params_str(lemmatization=False,
                                  stop_words_removal=False, punct_removal=False, tokenised_output=False,
                                  crop_first_lines=True):
    str_preprocess_params = ""
    if tokenised_output:
        str_preprocess_params += "tok_"
    if lemmatization:
        str_preprocess_params += "lemma_"
    if stop_words_removal:
        str_preprocess_params += "rmstop_"
    if punct_removal:
        str_preprocess_params += "rmpunct_"
    if crop_first_lines:
        str_preprocess_params += "crop_"

    return str_preprocess_params


def preprocess_and_save_df_to_csv(df: pd.DataFrame, dir_path: str, overwrite=False, lemmatization=False,
                                  stop_words_removal=False,
                                  stop_words_to_keep=None, punct_removal=False, tokenised_output=False,
                                  crop_first_lines=True):
    # verify if dir_path exists
    if not os.path.exists(dir_path):
        raise ValueError(f"dir_path {dir_path} does not exist")

    # search if csv file already exists in dir path
    csv_file_name = "df_lyrics_preprocessed_"

    csv_file_name += get_str_preprocess_params_str(lemmatization=lemmatization, stop_words_removal=stop_words_removal,
                                                   punct_removal=punct_removal, tokenised_output=tokenised_output,
                                                   crop_first_lines=crop_first_lines)

    csv_file_name += ".csv"
    csv_file_path = os.path.join(dir_path, csv_file_name)
    if os.path.exists(csv_file_path) and not overwrite:
        return csv_file_path
    else:
        df = preprocess_genius_lyrics_from_df(df, lemmatization=lemmatization, stop_words_removal=stop_words_removal,
                                              stop_words_to_keep=stop_words_to_keep, punct_removal=punct_removal,
                                              tokenised_output=tokenised_output, crop_first_lines=crop_first_lines,
                                              overwrite_lyrics_column=True)
    df.to_csv(csv_file_path, index=False)
    # print("Saved preprocessed lyrics in {}.".format(csv_file_path))
    return csv_file_path




# %%

# apply processing to all artists available
def preprocess_all_available_artists(ids, overwrite=False, lemmatization=False, stop_words_removal=False,
                                     stop_words_to_keep=None, punct_removal=False, tokenised_output=False,
                                     crop_first_lines=True):

    def do_task(id_):
        df = cdm.get_df_artist_lyrics_by_genius_id(id_)

        if df is not None and len(df) > 0:
            return preprocess_and_save_df_to_csv(df, cdm.available_artists_ids_paths[id_], overwrite=overwrite,
                                                 lemmatization=lemmatization, stop_words_removal=stop_words_removal,
                                                 stop_words_to_keep=stop_words_to_keep, punct_removal=punct_removal,
                                                 tokenised_output=tokenised_output, crop_first_lines=crop_first_lines)

        return None

    # use multithreading with 4 threads, concurrent.futures and display loading bar
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(tqdm(executor.map(do_task, ids), total=len(ids)))


def check_dir_contents(dir_path,id_, preprocess_params_str):
    no_csv_preprocessed = not glob(f'{dir_path}/*preprocessed_{preprocess_params_str}.csv', recursive=True)
    return id_, no_csv_preprocessed


# main
if __name__ == '__main__':
    OVERWRITE = False

    LEMMATIZATION = False
    STOP_WORDS_REMOVAL = False
    STOP_WORDS_TO_KEEP = []
    PUNCT_REMOVAL = True
    TOKENISED_OUTPUT = True
    CROP_FIRST_LINES = True
    params_str = get_str_preprocess_params_str(lemmatization=LEMMATIZATION,
                                               stop_words_removal=STOP_WORDS_REMOVAL,
                                               punct_removal=PUNCT_REMOVAL,
                                               tokenised_output=TOKENISED_OUTPUT,
                                               crop_first_lines=CROP_FIRST_LINES)
    # count number of dir with no csv preprocessed

    ids, no_csv_preprocesseds = zip(*[check_dir_contents(cdm.available_artists_ids_paths[id_],id_,params_str) for id_ in
                                                           cdm.available_artists_ids_paths.keys()])
    # filter ids from artists with no csv preprocessed

    ids_to_preprocess = [id_ for id_, no_csv_preprocessed in zip(ids, no_csv_preprocesseds) if no_csv_preprocessed] if not OVERWRITE else ids


    # demand user to preprocess all artists
    if len(ids_to_preprocess) > 0:
        response = input(f"Do you want to preprocess ({params_str}) {len(ids_to_preprocess)} artists ? (y/n)")
        if response != "y":
            exit()
        # launch preprocessing for all artists
        print("> Preprocessing...")
        preprocess_all_available_artists(ids_to_preprocess, overwrite=OVERWRITE, lemmatization=LEMMATIZATION,
                                         stop_words_removal=STOP_WORDS_REMOVAL, stop_words_to_keep=STOP_WORDS_TO_KEEP,
                                         punct_removal=PUNCT_REMOVAL, tokenised_output=TOKENISED_OUTPUT,
                                         crop_first_lines=CROP_FIRST_LINES)
        print("> Done.")
