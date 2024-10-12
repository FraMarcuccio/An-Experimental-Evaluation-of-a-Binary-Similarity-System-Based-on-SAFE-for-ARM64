import os
import logging
import numpy as np
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
logging.getLogger('tensorflow').disabled = True
import tensorflow as tf

from binsim_utility import *

class PairWiseSimilarity:

    def __init__(self, list_embeddings_1, list_embeddings_2, logger) -> None:
        self.logger = logger
        # Remember that list embeddings is a list of tuple of the form (id, horizontal np.array)
        # Need ids in the same order to be able to match embeddings with id function
        self.list_ids_1 = get_ids_from_functions(list_embeddings_1)
        self.list_ids_2 = get_ids_from_functions(list_embeddings_2)

        self.index_by_id_1 = dict()
        self.index_by_id_2 = dict()

        for i, id in enumerate(self.list_ids_1):
            self.index_by_id_1[id] = i
        
        for i, id in enumerate(self.list_ids_2):
            self.index_by_id_2[id] = i

        # prepare to build sim matrix
        self.list_embeddings_1 = list(map(lambda x: x[1], list_embeddings_1))
        self.list_embeddings_2 = list(map(lambda x: x[1], list_embeddings_2))

        self.ts_graph = tf.Graph()
        self.similarities = self._compute_similarity(self.list_embeddings_1, self.list_embeddings_2)
    
    def _compute_similarity(self, list_embeddings_1, list_embeddings_2):

        with self.ts_graph.as_default():
            tf.compat.v1.set_random_seed(1234)
            self.matrix_1     = tf.constant(np.asarray(list_embeddings_1), name='matrix_embeddings_1', dtype=tf.float32)
            self.matrix_2     = tf.constant(np.asarray(list_embeddings_2), name='matrix_embeddings_2', dtype=tf.float32)
            self.similarities = tf.matmul(self.matrix_1, self.matrix_2, transpose_b=True, name="embeddings_similarities")
            self.session = tf.compat.v1.Session()
            return self.session.run(self.similarities)
    
    # Take cue to create a similar function, matrices and submatrices to look for better match
    def get_max_match(self, list_functions_1, list_functions_2):
        try:
            # Make sure IDs are strings and convert if necessary.
            rows = [self.index_by_id_1[str(f[0])] for f in list_functions_1]
            cols = [self.index_by_id_2[str(f[0])] for f in list_functions_2]
        except KeyError as e:
            self.logger.error(f"KeyError: {e}")
            self.logger.error(f"List functions 1: {[str(f[0]) for f in list_functions_1]}")
            self.logger.error(f"List functions 2: {[str(f[0]) for f in list_functions_2]}")
            self.logger.error(f"Index by ID 1: {self.index_by_id_1.keys()}")
            self.logger.error(f"Index by ID 2: {self.index_by_id_2.keys()}")
            raise

        # Verify that the indexes are valid
        if any(row >= len(self.similarities) for row in rows) or any(col >= len(self.similarities[0]) for col in cols):
            self.logger.error("[get_max_match] Indices out of bounds")
            return None, None, None

        # Creates an array of submatrices with the given indexes
        sub_indices = np.ix_(rows, cols)
        similarities_sub_matrix = self.similarities[sub_indices]

        # Find the maximum similarity
        max_similarity = np.amax(similarities_sub_matrix)
        r_list, c_list = np.where(similarities_sub_matrix == max_similarity)

        if len(r_list) == 0 or len(c_list) == 0 or len(r_list) != len(c_list):
            self.logger.error("[get_max_match] max found but r_list and c_list are empty or mismatched")
            return None, None, None

        r, c = r_list[0], c_list[0]

        return list_functions_1[r], list_functions_2[c], max_similarity

    # Modified from the original slightly
    def get_fuzzy_matches(self, threshold):
        if isinstance(self.similarities, tf.Tensor):
            self.similarities = self.similarities.numpy()  # Convert TensorFlow tensor to NumPy array

        fuzzy_matches = []
        n = min(len(self.list_ids_1), len(self.list_ids_2))
        matrix = np.copy(self.similarities)

        while n > 0:
            max_score = np.amax(matrix)
            if max_score < threshold:
                return fuzzy_matches

            rows, cols = np.where(matrix == max_score)
            r, c = rows[0], cols[0]

            n -= 1
            fuzzy_matches.append((self.list_ids_1[r], self.list_ids_2[c], max_score))
            matrix = np.delete(matrix, r, axis=0)
            matrix = np.delete(matrix, c, axis=1)

        return fuzzy_matches