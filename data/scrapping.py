from todo_utils import get_todo_list, get_done_list, is_already_done, sort_text_file, add_to_done_list
import os


def main() -> None:
    # ---- QUERIES
    queries_todo = get_todo_list()
    queries_done = get_done_list()
    # get difference between queries todo and dones
    diff = queries_todo.difference(queries_done)
    print(f"queries: {len(queries_done) / len(queries_todo):.2%}")

    # ---- IDS
    ids_todo = get_todo_list("ids")
    ids_done = get_done_list("ids")
    # get difference between ids todo and dones
    diff = ids_todo.difference(ids_done)
    print(f"ids: {len(ids_done) / len(ids_todo):.2%}")

    for query in queries_todo:
        if not is_already_done(query):
            script = f'python lyrics_scrapper.py -qa "{query}"'
            print(f" * Start of script * : '{script}'")
            if os.system(script) == 0:
                print(f" ** End of script ** : '{script}'")
                add_to_done_list(query, "queries")
            else:
                print(f" * Error in script * : '{script}'")

    sort_text_file("todo/queries_done.txt")
    sort_text_file("todo/queries_todo.txt")

    for id in ids_todo:
        if not is_already_done(id, "ids"):
            script = f'python lyrics_scrapper.py -id "{id}"'
            print(f" * Start of script * : '{script}'")
            if os.system(script) == 0:
                print(f" ** End of script ** : '{script}'")
                add_to_done_list(id, "ids")
            else:
                print(f" * Error in script * : '{script}'")

    sort_text_file("todo/ids_done.txt")
    sort_text_file("todo/ids_todo.txt")


if __name__ == '__main__':
    main()
