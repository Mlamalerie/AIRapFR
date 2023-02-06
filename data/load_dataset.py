import pickle, os
from glob import glob


def load_dataset_with_pickle(dataset_dir_path, rap_corpus=True, artist_name_focus=""):
    # verify if dataset exist
    if not os.path.isdir(dataset_dir_path):
        raise ValueError(f"dataset_dir_path {dataset_dir_path} does not exist")

    # load dataset rap corpus with pickle
    query = os.path.join(dataset_dir_path, f"{artist_name_focus if not rap_corpus else 'rap_corpus'}*.pkl")
    if file_path_data := glob(query):
        with open(file_path_data[0], 'rb') as f:
            sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict, _, len_dataset = pickle.load(
                f)
    else:
        raise ValueError(f"file_path_data {file_path_data} {query} does not exist")
    # get word index dict
    if file_word_index_dict := glob(os.path.join(dataset_dir_path, "word_index_dict*.pkl")):
        with open(file_word_index_dict[0], 'rb') as f:
            word_index_dict_union = pickle.load(f)

    print("Loaded dataset with pickle from {}.".format(file_path_data[0]))
    print(f" > len(full_dataset): {len_dataset}")
    print(f" > len(train): {len(sentences_train)} # {sentences_train[0]} {next_words_train[0]} " )
    print(f" > len(test): {len(sentences_test)} # {sentences_test[0]} {next_words_test[0]} " )
    print(f" > len(set_words): {len(set_words)} # {list(set_words)[:10]} " )
    print(f" > len(word_index_dict): {len(word_index_dict)} # {list(word_index_dict.items())[:5]} " )


    return sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict_union, len_dataset


if __name__ == '__main__':
    dataset_dir_path = "datasets/dataset-1273-keryjames-20230206"
    sentences_train, next_words_train, sentences_test, next_words_test, set_words, word_index_dict_union, len_dataset = load_dataset_with_pickle(
        dataset_dir_path, rap_corpus=True, artist_name_focus="keryjames")
# %%
