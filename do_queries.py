import os


# verify if artist query is already done
def is_query_already_done(query):
    with open("queries_done.txt", encoding='utf-8') as f:
        for readline in f:
            line_strip = readline.strip()
            if line_strip.lower() == query.lower():
                return True
    return False

# get artist query from done list
def get_queries_todo_list():
    result = []
    with open("queries_todo.txt", encoding='utf-8') as f:
        result.extend(readline.strip() for readline in f)
    return set(result)

if __name__ == '__main__':
    if queries := get_queries_todo_list():
        for query in queries:
            if not is_query_already_done(query):
                script = f'python data_lyrics.py -qa "{query}"'
                print(f" * Start of script * : '{script}'")
                if os.system(script) == 0:
                    print(f" ** End of script ** : '{script}'")
                else:
                    print(f" * Error in script * : '{script}'")
    