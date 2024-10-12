import numpy as np

def embeddingToNp(e):
    e = e.replace('\n', '')
    e = e.replace('[', '')
    e = e.replace(']', '')
    emb = np.fromstring(e, dtype=float, sep=' ')
    return emb

def get_ids_from_functions(functions):
    return list(map(lambda x: x[0], functions))

def get_indeces(to_find_list, container_list):
    indeces = [container_list.index(id) for id in to_find_list]

    if len(indeces) != len(to_find_list):
        # The program must be crashed. No catching it!
        raise Exception("Input list is not a subset of container list")
    else:
        return indeces