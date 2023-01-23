import os


# verify if artist query is already done

def sort_text_file(file_path : str):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    lines = set(lines)
    lines = sorted(lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# get artist query from done list
def get_todo_list(what="queries"):
    result = []
    with open(f"todo_scrap/{what}_todo.txt", encoding='utf-8') as f:
        result.extend(readline.strip() for readline in f)
    return set(result)


def get_done_list(what="queries"):
    result = []
    with open(f"todo_scrap/{what}_done.txt", encoding='utf-8') as f:
        result.extend(readline.strip() for readline in f)
    return set(result)


def is_already_done(x,what="queries"):
    with open(f"todo_scrap/{what}_done.txt", encoding='utf-8') as f:
        for readline in f:
            line_strip = readline.strip()
            if line_strip.lower() == x.lower():
                return True
    return False


if __name__ == '__main__':

    # ---- QUERIES
    queries_todo = get_todo_list()
    queries_done = get_done_list()
    # get difference between queries todo and dones
    diff = queries_todo.difference(queries_done)
    print(f"queries: {len(queries_done)/len(queries_todo):.2%}")

    # ---- IDS
    ids_todo = get_todo_list("ids")
    ids_done = get_done_list("ids")
    # get difference between ids todo and dones
    diff = ids_todo.difference(ids_done)
    print(f"ids: {len(ids_done)/len(ids_todo):.2%}")



    if queries_todo := get_todo_list():
        for query in queries_todo:
            if not is_already_done(query):
                script = f'python data_lyrics.py -qa "{query}"'
                print(f" * Start of script * : '{script}'")
                if os.system(script) == 0:
                    print(f" ** End of script ** : '{script}'")
                else:
                    print(f" * Error in script * : '{script}'")

    sort_text_file("todo_scrap/queries_done.txt")
    sort_text_file("todo_scrap/queries_todo.txt")

    