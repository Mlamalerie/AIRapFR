from glob import glob
# get all dirs in corpus
import os
from tqdm import tqdm
import argparse
def get_all_dirs(base_dir_path: str) -> list:
    if dirs := glob(f"{base_dir_path}/*"):
        return dirs
    return None

# select all json files in a directory
def get_all_json_files(dir_path: str) -> list:
    if files := glob(f"{dir_path}/*.json"):
        return files
    return []

# delete a list of files
def delete_files(files: list) -> None:

    for file in files:
        if os.path.exists(file):
            os.remove(file)

# todo : delete english lyrics
def main() -> None:
    # parse
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--yes", help="Delete all json files without asking for confirmation.", default=None)
    args = parser.parse_args()

    corpus_dir = "corpus"
    dirs = get_all_dirs(corpus_dir)
    total_json_files = sum([len(get_all_json_files(dir)) for dir in dirs])
    print(f"Found {len(dirs)} directories in {corpus_dir} -> {total_json_files} json files in total.")
    if total_json_files == 0:
        return
    if args.yes:
        response = "y"
    else:
        response = input(f"Do you want to delete all json files [{total_json_files}] in these directories? (y/n)")

    if response != "y":
        return
    for dir in tqdm(dirs, total=len(dirs)):
        files = get_all_json_files(dir)
        delete_files(files)


if __name__ == "__main__":
    main()