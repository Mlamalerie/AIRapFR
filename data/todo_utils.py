def sort_text_file(file_path: str):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    lines = set(lines)
    lines = sorted(lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


# get artist query from done list
def get_todo_list(what="queries"):
    result = []
    with open(f"todo/{what}_todo.txt", encoding='utf-8') as f:
        result.extend(readline.strip() for readline in f)
    return set(result)


def get_done_list(what="queries"):
    result = []
    with open(f"todo/{what}_done.txt", encoding='utf-8') as f:
        result.extend(readline.strip() for readline in f)
    return set(result)


# verify if artist query is already done

def is_already_done(x, what="queries"):
    with open(f"todo/{what}_done.txt", encoding='utf-8') as f:
        for readline in f:
            line_strip = readline.strip()
            if line_strip.lower() == x.lower():
                return True
    return False


# add artist query to done list
def add_to_done_list(query, what="queries"):
    if not is_already_done(query, what):
        with open(f"todo/{what}_done.txt", "a", encoding='utf-8') as f:
            f.write(f"{query}\n")
