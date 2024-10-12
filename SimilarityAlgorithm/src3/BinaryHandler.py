import os
import sqlite3
import json
import networkx as nx
from capstone import *
from capstone.arm64 import *
from Analysis import DatabaseFunctionAnalyzer, InstructionsConverter, FunctionNormalizer, SAFEEmbedder
from PairWiseSimilarity import PairWiseSimilarity
import pprint
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from node2vec import Node2Vec
from networkx.algorithms.similarity import graph_edit_distance

class BinaryHandler:

    def compute_fuzzy_similarity(prof_common, embeddings1_unmatched, embeddings2_unmatched, threshold):
        """
        Compute fuzzy similarity between unmatched embeddings of two sets of functions.
        
        :param prof_common: PairWiseSimilarity object initialized with common functions embeddings
        :param embeddings1_unmatched: List of unmatched embeddings from the first file
        :param embeddings2_unmatched: List of unmatched embeddings from the second file
        :param threshold: Similarity threshold for fuzzy matching
        :return: List of fuzzy matches and the weighted average similarity
        """
        if not embeddings1_unmatched or not embeddings2_unmatched:
            return [], 0.0

        fuzzy_matches = prof_common.get_fuzzy_matches(threshold)
        
        coverage_1 = len(fuzzy_matches) / len(embeddings1_unmatched) if embeddings1_unmatched else 0
        coverage_2 = len(fuzzy_matches) / len(embeddings2_unmatched) if embeddings2_unmatched else 0

        average_similarity = 0 if not fuzzy_matches else sum(similarity for _, _, similarity in fuzzy_matches) / len(fuzzy_matches)

        weighted_avg_similarity = (average_similarity * coverage_1 + average_similarity * coverage_2) / 2

        return fuzzy_matches, weighted_avg_similarity

    def find_best_match(similarity_matrix, functions1, functions2):
        """
        Finds the best match between two sets of functions based on similarity.
        
        Args:
        - similarity_matrix (numpy.ndarray): Similarity matrix between the functions.
        - functions1 (list): List of functions from the first file.
        - functions2 (list): List of functions from the second file.

        Returns:
        - tuple: The best match with the function names and maximum similarity.
        """
        # Finds max similarity
        max_similarity = np.amax(similarity_matrix)
        r_list, c_list = np.where(similarity_matrix == max_similarity)

        if len(r_list) == 0 or len(c_list) == 0 or len(r_list) != len(c_list):
            print("[find_best_match] max found but r_list and c_list are empty or mismatched")
            return None, None, None

        r, c = r_list[0], c_list[0]

        return functions1[r]['function_name'], functions2[c]['function_name'], max_similarity

    def find_best_match_unmatched(similarity_matrix, embeddings1, embeddings2):
        """
        Finds the best match between two sets of embeddings based on the similarity matrix.
        
        Parameters:
        - similarity_matrix (np.ndarray): Similarity matrix of size (n, m),
        where n is the number of embeddings in embeddings1 and m is the number of embeddings in embeddings2.
        - embeddings1 (list): List of embeddings from the first set.
        - embeddings2 (list): List of embeddings from the second set.

        Returns:
        - best_matches (list of tuples): List of tuples, where each tuple contains the index of the embedding
        from embeddings1 and the index of the embedding from embeddings2 that represent the best match.
        - max_similarity (float): The maximum similarity found.
        """
        num_embeddings1 = similarity_matrix.shape[0]
        num_embeddings2 = similarity_matrix.shape[1]

        # Finds max similarity
        max_similarity = np.amax(similarity_matrix)

        # Finds the positions (rows, columns) where the maximum value is located
        r_list, c_list = np.where(similarity_matrix == max_similarity)

        # Verifies that the row and column lists are valid and have the same number of elements
        if len(r_list) == 0 or len(c_list) == 0 or len(r_list) != len(c_list):
            print("[find_best_match] max found but r_list and c_list are empty or mismatched")
            return None, None

        # Taking first match
        r, c = r_list[0], c_list[0]

        # Return the best matches and maximum similarity.
        best_matches = [(r, c)]
        return best_matches, max_similarity

    def calculate_bfs_dfs_similarities(functions1, functions2):
        bfs_dfs_similarities_common = []
        for common_func_key in functions1.keys() & functions2.keys():
            func1 = functions1[common_func_key]
            func2 = functions2[common_func_key]
            bfs_dfs_similarity = BinaryHandler.compute_bfs_dfs_similarity_as_graph(
                func1['bfs_result'], func1['dfs_result'],
                func2['bfs_result'], func2['dfs_result']
            )
            bfs_dfs_similarities_common.append((common_func_key, bfs_dfs_similarity))

        bfs_dfs_similarities_unmatched = []
        unmatched_functions1 = [functions1[k] for k in functions1.keys() - functions2.keys()]
        unmatched_functions2 = [functions2[k] for k in functions2.keys() - functions1.keys()]

        for unmatched_func in unmatched_functions1:
            for other_func in unmatched_functions2:
                bfs_dfs_similarity = BinaryHandler.compute_bfs_dfs_similarity_as_graph(
                    unmatched_func['bfs_result'], unmatched_func['dfs_result'],
                    other_func['bfs_result'], other_func['dfs_result']
                )
                bfs_dfs_similarities_unmatched.append(((unmatched_func['function_name'], other_func['function_name']), bfs_dfs_similarity))
        
        return bfs_dfs_similarities_common, bfs_dfs_similarities_unmatched

    def normalize_similarity(value):
        """
        Normalizes the similarity value between 0 and 1.
        :param value: Similarity value to normalize.
        :return: Normalized value between 0 and 1.
        """
        return max(0, min(1, value))

    # Uses edith_distance approximated with timeout time.
    def graph_similarity(graph1, graph2):
        """
        Calculates the similarity between two graphs using an approximated graph edit distance.

        :param graph1: First graph (NetworkX graph)
        :param graph2: Second graph (NetworkX graph)
        :return: Normalized similarity score
        """
        if graph1 is None or graph2 is None:
            print("One of the graphs is None. Returning a similarity score of 0.")
            return 0

        if len(graph1.nodes) == 0 or len(graph2.nodes) == 0:
            print("One of the graphs is empty. Returning a similarity score of 0.")
            return 0

        try:
            # Calculates the approximated graph edit distance with a timeout of 5 seconds
            edit_distance = nx.graph_edit_distance(graph1, graph2, timeout=5)
            
            if edit_distance is None:
                # If the timeout expired, assume a very large distance
                edit_distance = max(graph1.number_of_nodes(), graph2.number_of_nodes())
                
        except nx.NetworkXError as e:
            print(f"NetworkX Error: {e}")
            return 0

        # Normalizes the edit distance to calculate similarity
        max_possible_distance = max(graph1.number_of_nodes(), graph2.number_of_nodes())
        
        if max_possible_distance == 0:
            print("The maximum possible distance is zero. Unable to calculate similarity.")
            return 0
        
        similarity = 1 - (edit_distance / max_possible_distance)
        
        # Normalizzazione da 0 a 1
        return BinaryHandler.normalize_similarity(similarity)

    def compute_bfs_dfs_similarity_as_graph(bfs_result1, dfs_result1, bfs_result2, dfs_result2):
        """
        Calculates the similarity between the BFS and DFS results of two functions using a graph-based approach.

        :param bfs_result1: BFS result of the first function (list of hexadecimal strings)
        :param dfs_result1: DFS result of the first function (list of hexadecimal strings)
        :param bfs_result2: BFS result of the second function (list of hexadecimal strings)
        :param dfs_result2: DFS result of the second function (list of hexadecimal strings)
        :return: Similarity score
        """
        def create_graph_from_results(results):
            G = nx.Graph()
            for idx, node in enumerate(results):
                G.add_node(node)
                if idx > 0:
                    G.add_edge(results[idx - 1], node)
            return G

        # Create graphs from BFS and DFS results
        G1_bfs = create_graph_from_results(bfs_result1)
        G2_bfs = create_graph_from_results(bfs_result2)
        G1_dfs = create_graph_from_results(dfs_result1)
        G2_dfs = create_graph_from_results(dfs_result2)

        # Calculate graph similarities using edit distance
        bfs_similarity = BinaryHandler.graph_similarity(G1_bfs, G2_bfs)
        dfs_similarity = BinaryHandler.graph_similarity(G1_dfs, G2_dfs)

        # Combine similarities
        return (bfs_similarity + dfs_similarity) / 2

    def calculate_final_similarities(bfs_dfs_similarities_common, bfs_dfs_similarities_unmatched, common_similarity_threshold=0.8, unmatched_similarity_threshold=0.2):
        # Counts the functions with high similarity in common functions
        high_similarity_common = sum(1 for _, similarity in bfs_dfs_similarities_common if similarity > common_similarity_threshold)

        # Counts the functions with high similarity in unmatched functions
        high_similarity_unmatched = sum(1 for _, similarity in bfs_dfs_similarities_unmatched if similarity > unmatched_similarity_threshold)

        # Total number of common functions analyzed
        total_common_functions = len(bfs_dfs_similarities_common)

        # Total number of unmatched functions analyzed
        total_unmatched_functions = len(bfs_dfs_similarities_unmatched)

        # Calculate the final similarity for common functions
        final_similarity_common = (high_similarity_common / total_common_functions) if total_common_functions > 0 else 0.0

        # Calculate the final similarity for unmatched functions
        final_similarity_unmatched = (high_similarity_unmatched / total_unmatched_functions) if total_unmatched_functions > 0 else 0.0

        return final_similarity_common, final_similarity_unmatched
