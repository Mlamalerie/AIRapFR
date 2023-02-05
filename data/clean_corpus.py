from datetime import datetime
from glob import glob
# get all dirs in corpus
import os
from tqdm import tqdm
from data.lyrics_scrapper import get_df_from_one_json_file, get_df_from_all_json_files
import argparse
def get_all_dirs(base_dir_path: str) -> list:
    return dirs if (dirs := glob(f"{base_dir_path}/*")) else None

# select all json files in a directory
def get_all_json_files(dir_path: str) -> list:
    return files if (files := glob(f"{dir_path}/*.json")) else []

# delete a list of files
def delete_files(files: list) -> None:

    for file in files:
        if os.path.exists(file):
            os.remove(file)

def check_dir_content(dir_path): #move this fonction to lyrics csrapper
    no_jsons_in_dir = not glob(f'{dir_path}/[Ll]yrics_*.json', recursive=True)
    no_csv_concat_in_dir = not glob(f'{dir_path}/df_genius*.csv', recursive=True)
    no_csv_preprocessed = not glob(f'{dir_path}/*preprocessed*.csv', recursive=True )
    return no_jsons_in_dir, no_csv_concat_in_dir,no_csv_preprocessed

def check_all_dirs_and_create_csv_concat(dir_paths: list) -> None:
    count = 0
    dirs_to_delete = []
    for dir in tqdm(dir_paths, total=len(dir_paths)):
        no_jsons_in_dir, no_csv_concat_in_dir,no_csv_preprocessed = check_dir_content(dir)
        if not no_jsons_in_dir and no_csv_concat_in_dir and no_csv_preprocessed:
            #print(f"Creating csv concat for {dir}")
            df_all_songs = get_df_from_all_json_files(dir)
            artist_name = os.path.basename(dir).split("-")[-1]
            #print(f"Saving csv concat for {artist_name}")

            df_output_file = f"""{dir}/df_genius_{artist_name}_all_songs_{datetime.now().strftime("%Y%m")}.csv"""

            df_all_songs.to_csv(df_output_file, index=False)
            count += 1
        elif no_jsons_in_dir and no_csv_concat_in_dir and no_csv_preprocessed:
            dirs_to_delete.append(dir)
    print(f"Done : Created csv concat for each {count} directories.")

    # delete empty dirs
    print(f"Deleting {len(dirs_to_delete)} empty directories.")
    for dir_to_delete in dirs_to_delete:
        os.rmdir(dir_to_delete)
def main() -> None:
    # parse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", help="Delete all json files without asking for confirmation.", default=False)
    args = parser.parse_args()

    corpus_dir = "corpus"
    dir_paths_corpus = get_all_dirs(corpus_dir)


    # 1. check if user wants to create csv concat with json files solo
    total_dir_with_no_csv_concat = sum(
        check_dir_content(dir)[1] for dir in dir_paths_corpus
    )

    print(f"> Found {total_dir_with_no_csv_concat} directories with no csv concat.")
    if total_dir_with_no_csv_concat > 0:
        if args.force:
            response = "y"
        else:
            response = input(f"Do you want to create csv concat for {total_dir_with_no_csv_concat} directories? (y/n) ")

        if response == "y":
            check_all_dirs_and_create_csv_concat(dir_paths_corpus)

    # 2. check if user wants to delete all json files
    total_json_files = sum(
        len(get_all_json_files(dir)) for dir in dir_paths_corpus
    )
    print(f"> Found {len(dir_paths_corpus)} directories in {corpus_dir} -> {total_json_files} json files in total.")
    # check total json files in corpus
    if total_json_files > 0:

        if args.force:
            response = "y"
        else:
            response = input(f"Do you want to delete all json files [{total_json_files}] in these directories? (y/n)")

        if response == "y":
            for dir in tqdm(dir_paths_corpus, total=len(dir_paths_corpus)):
                if files := get_all_json_files(dir):
                    delete_files(files)


if __name__ == "__main__":
    main()