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


text = """[Intro] (Rohff)
    
    [Refrain] (Rohff) 
    J'suis né poussière et j'repartirai poussière \xa0
    Et le soleil se lèvera en même temps que la misère, frère
    T'es parti, t'étais là devant moi à me parler de Ya Rabi
    Tu venais d'te mettre à faire la ière-pri
    Que Dieu te préserve des châtiments
    Après la vie c'est autrement et la rue perd ses monuments
    Perd ses valeurs, perd ses principes
    Perd son respect de la discipline dans l'illicite
    Les peines s'alourdissent des assises aux cercueils
    Un article en page faits divers, une hajja en deuil
    Les femmes de la famille autour pour la soutenir
    Du chagrin de son fils qu'elle    a vu sortir
    Pour plus jamais revenir
    """


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
    #df[column_name] = df['lyrics'].progress_apply(f_preprocessing)
    df[column_name] = df['lyrics'].apply(f_preprocessing)
    # df["lyrics_preprocessed"] = df['lyrics'].parallel_apply(f_preprocessing)

    return df


# new_df = preprocess_genius_lyrics_from_df(df)

# %%
def preprocess_and_save_df_to_csv(df: pd.DataFrame, dir_path: str, overwrite=False, lemmatization=False,
                                  stop_words_removal=False,
                                  stop_words_to_keep=None, punct_removal=False, tokenised_output=False,
                                  crop_first_lines=True):
    # verify if dir_path exists
    if not os.path.exists(dir_path):
        raise ValueError(f"dir_path {dir_path} does not exist")

    # search if csv file already exists in dir path
    csv_file_name = "df_lyrics_preprocessed_"
    if tokenised_output:
        csv_file_name += "tok_"
    if lemmatization:
        csv_file_name += "lemma_"
    if stop_words_removal:
        csv_file_name += "rmstop_"
    if punct_removal:
        csv_file_name += "rmpunct_"
    if crop_first_lines:
        csv_file_name += "crop_"

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
        #print("Saved preprocessed lyrics in {}.".format(csv_file_path))
        return csv_file_path

"""
id_ = cdm.get_id_by_artist_name("Rohff")
preprocess_and_save_df_to_csv(df, cdm.available_artists_ids_paths[id_], overwrite=False, lemmatization=False,
                              stop_words_removal=False, stop_words_to_keep=[], punct_removal=False,
                              tokenised_output=True,
                              crop_first_lines=True)
"""

# %%

# apply processing to all artists available
def preprocess_all_available_artists(overwrite=False, lemmatization=False, stop_words_removal=False,
                           stop_words_to_keep=None, punct_removal=False, tokenised_output=False,
                           crop_first_lines=True):
    ids = list(cdm.available_artists_ids_paths.keys())#[:20]

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



# main
if __name__ == '__main__':
    print("Preprocessing all available artists...")
    preprocess_all_available_artists(overwrite=False, lemmatization=False, punct_removal=True,
                                      tokenised_output=True,
                                      crop_first_lines=True)
    print("Done.")


