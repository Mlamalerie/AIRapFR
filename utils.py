import math
import os
import re
import time
import typing as Optional
import unicodedata
from difflib import SequenceMatcher


def create_dir(where: str, name_new_folder: Optional.Union[str, None] = None, sleep_sec: int = 1):
    new_folder_path = f"{where}/{name_new_folder}" if name_new_folder else where
    if not os.path.exists(new_folder_path) or not os.path.isdir(new_folder_path):
        os.mkdir(new_folder_path)
        if sleep_sec > 0:
            time.sleep(sleep_sec)
    return new_folder_path


def display_loading(txt: str, nb: int, max: int) -> None:
    # display loading bar
    percent = float(nb / max * 100)

    print("\r[", end="")
    cubes = percent / 10
    i = 0
    while i < math.floor(cubes):
        print(u"\u25A0", end="")
        i += 1
    while i < 10:
        print(u"\u25A1", end="")
        i += 1
    print("] - " + "%.1f" % percent + f"% {txt}", end="")


def remove_accented_chars(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return text


def simplify_text(text, keep_digits=False, substitute=""):
    """
    Simplify text by removing accents and special characters and lowercasing
    :param text:
    :param keep_digits:
    :return:
    """
    return (
        re.sub("[^a-zA-Z0-9]+", "", remove_accented_chars(text).lower())
        if keep_digits
        else re.sub("[^a-zA-Z]+", "", remove_accented_chars(text).lower())
    )


# split my text with many separators
def split_text_with_separators(text, separators):
    regexPattern = '|'.join(map(re.escape, separators))
    return [e for e in re.split(regexPattern, text) if e]


# filter my list with a regex
def filter_str_list(str_list, pattern):
    return [e for e in str_list if re.match(pattern, e)]


# compare two string, return score between 0 and 1
def compare_str(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()
