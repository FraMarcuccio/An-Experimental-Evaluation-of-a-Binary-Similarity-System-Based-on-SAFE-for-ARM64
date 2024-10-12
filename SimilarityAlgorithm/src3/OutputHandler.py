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

class OutputPrinter:
    @staticmethod
    def print_file_comparison(file_info):
        print(f"File1: {file_info['file1']} - File2: {file_info['file2']}")
        OutputPrinter.print_common_functions(file_info)
        OutputPrinter.print_embedding_comparisons(file_info)
        OutputPrinter.print_max_similarity_common(file_info)
        OutputPrinter.print_fuzzy_matches(file_info)
        OutputPrinter.print_max_fuzzy_match(file_info)
        OutputPrinter.print_component_sizes(file_info)
        OutputPrinter.print_bfs_dfs_similarities_common(file_info)
        OutputPrinter.print_bfs_dfs_similarities_unmatched(file_info)
        print("-" * 40)

    @staticmethod
    def print_common_functions(file_info):
        print("Common functions:")
        for func in file_info['common_functions']:
            print(f"  Function Name: {func['function_name']}")

    @staticmethod
    def print_embedding_comparisons(file_info):
        print("Embedding Comparisons for Common Functions:")
        for comp in file_info['embedding_comparisons']:
            func_name, similarity = comp  # `func_key` is only a single name function
            print(f"  Function {func_name}: Similarity: {similarity}")

    @staticmethod
    def print_max_similarity_common(file_info):
        print("Max Similarity for Common Functions:")
        func1_name, func2_name, max_similarity = file_info['max_similarity_common']
        print(f"  Functions {func1_name} and {func2_name} with similarity {max_similarity}")

    @staticmethod
    def print_fuzzy_matches(file_info):
        print("Fuzzy Matches:")
        for match in file_info['fuzzy_matches']:
            func1_name, func2_name, similarity = match
            print(f"  Function {func1_name} - {func2_name}: Similarity: {similarity}")

    @staticmethod
    def print_max_fuzzy_match(file_info):
        func_name = file_info.get('max_fuzzy_match', None)
        max_fuzzy_similarity = file_info.get('max_sim_unmatch', None)
        if func_name is not None and max_fuzzy_similarity is not None:
            print(f"  Function {func_name} with similarity {max_fuzzy_similarity}")
        else:
            print("  No fuzzy match found for unmatched functions.")

    @staticmethod
    def print_component_sizes(file_info):
        print(f"Number of matched functions: {len(file_info['common_functions'])}")
        print(f"Number of unmatched functions in {file_info['file1']}: {len(file_info['unmatched_functions_file1'])}")
        print(f"Number of unmatched functions in {file_info['file2']}: {len(file_info['unmatched_functions_file2'])}")
        print(f"Number of left_connected in {file_info['file1']}: {len(file_info['component_size_file1'])} "
              f"VS Number of left_connected in {file_info['file2']}: {len(file_info['component_size_file2'])}")

    @staticmethod
    def print_bfs_dfs_similarities_common(file_info):
        print("BFS and DFS Similarities for Common Functions:")
        for bfs_dfs_similarity in file_info['bfs_dfs_similarities_common']:
            func_name, similarity = bfs_dfs_similarity  # `func_name` is unique
            print(f"  Function {func_name}: BFS and DFS Similarity: {similarity}")

    @staticmethod
    def print_bfs_dfs_similarities_unmatched(file_info):
        print("BFS and DFS Similarities for Unmatched Functions:")
        for bfs_dfs_similarity in file_info['bfs_dfs_similarities_unmatched']:
            func_name, similarity = bfs_dfs_similarity  # Considering `func_name` as a single element
            print(f"  Function {func_name}: BFS and DFS Similarity: {similarity}")

    @staticmethod
    def print_top_similar_files(comparison_result):
        max_diff_namef_common = {'files': None, 'similarity': 0}
        max_same_namef_common = {'files': None, 'similarity': 0}
        max_diff_namef = {'files': None, 'similarity': 0}
        max_same_namef = {'files': None, 'similarity': 0}

        for file_info in comparison_result:
            file1 = file_info['file1']
            file2 = file_info['file2']
            namef1 = file_info['namef1']
            namef2 = file_info['namef2']
            weighted_avg_similarity_common = file_info['weighted_avg_similarity_common']
            weighted_avg_similarity = file_info['weighted_avg_similarity']

            if namef1 != namef2:
                if weighted_avg_similarity_common > max_diff_namef_common['similarity']:
                    max_diff_namef_common = {'files': (file1, file2), 'similarity': weighted_avg_similarity_common}
                if weighted_avg_similarity > max_diff_namef['similarity']:
                    max_diff_namef = {'files': (file1, file2), 'similarity': weighted_avg_similarity}
            else:
                if weighted_avg_similarity_common > max_same_namef_common['similarity']:
                    max_same_namef_common = {'files': (file1, file2), 'similarity': weighted_avg_similarity_common}
                if weighted_avg_similarity > max_same_namef['similarity']:
                    max_same_namef = {'files': (file1, file2), 'similarity': weighted_avg_similarity}

        OutputPrinter._print_top_file_pair("Files with different namef having highest weighted_avg_similarity_common:", max_diff_namef_common)
        OutputPrinter._print_top_file_pair("Files with different namef having highest weighted_avg_similarity_fuzzy:", max_diff_namef)
        OutputPrinter._print_top_file_pair("Files with same namef having highest weighted_avg_similarity_common:", max_same_namef_common)
        OutputPrinter._print_top_file_pair("Files with same namef having highest weighted_avg_similarity_fuzzy:", max_same_namef)

    @staticmethod
    def _print_top_file_pair(description, top_file_pair):
        if top_file_pair['files']:
            print(description)
            print(f"File1: {top_file_pair['files'][0]}, File2: {top_file_pair['files'][1]}, Similarity: {top_file_pair['similarity']}")
        else:
            print(f"No files found for {description.lower()}")

    @staticmethod
    def print_hotspot_similarity(comparison_result):
        print("File pairs with highest hotspot similarity:")
        for file1, file2, similarity_list, avg_similarity in comparison_result:
            print(f"File1: {file1}, File2: {file2}, Average Similarity: {avg_similarity:.4f}")
            print("Detailed similarities between hotspots:")
            for hotspot1, hotspot2, similarity in similarity_list:
                print(f"  {hotspot1['function_name']} ({file1}) vs {hotspot2['function_name']} ({file2}) - Similarity: {similarity:.4f}")

    @staticmethod
    def print_top_bfs_dfs(top_bfs_dfs_common, top_bfs_dfs_unmatched):
        print("Top file pair with highest BFS and DFS similarities for common functions:")
        for file1, file2, avg_similarity in top_bfs_dfs_common:
            print(f"File1: {file1}, File2: {file2}, Average BFS and DFS Similarity: {avg_similarity:.4f}")

        print("Top file pair with highest BFS and DFS similarities for unmatched functions:")
        for file1, file2, avg_similarity in top_bfs_dfs_unmatched:
            print(f"File1: {file1}, File2: {file2}, Average BFS and DFS Similarity: {avg_similarity:.4f}")
        print("-" * 40)

    # Print all hotspots found by file
    def print_hotspots(hotspot_data, dataset_name):
        print(f"Hotspots found for {dataset_name}:")
        for filename, hotspots in hotspot_data.items():
            print(f"File: {filename}")
            for hotspot in hotspots:
                print(f"  Function: {hotspot['function_name']}")
                print(f"    Entry Point: {hotspot['entry_point']}")
                print(f"    Degree: {hotspot['degree']}")
                print(f"    Predecessor Degrees: {hotspot.get('predecessor_degrees', 'N/A')}")
                print(f"    Successor Degrees: {hotspot.get('successor_degrees', 'N/A')}")
                print(f"    Total Connected Degree: {hotspot.get('total_connected_degree', 'N/A')}")
                print(f"    Predecessors: {hotspot['predecessors']}")
                print(f"    Successors: {hotspot['successors']}")
            print("\n")

    @staticmethod
    def maps_similarity_scores_hotspot(hotspot_comparison_result):
        # Map files to hotspot similarity scores
        print("\nHotspot Similarity Scores:")
        hotspot_similarity_scores = {
            f"{file1}_{file2}": avg_similarity
            for file1, file2, _, avg_similarity in hotspot_comparison_result
        }
        for key, score in hotspot_similarity_scores.items():
            print(f"{key}: {score:.4f}")

        return hotspot_similarity_scores

    @staticmethod
    def print_comparison_results(hotspot_comparison_result):
        print("\nComparison of similarity between hotspots:")
        for comparison in hotspot_comparison_result:
            file1, file2, similarity_list, avg_similarity = comparison
            print(f"Comparison between {file1} and {file2}:")
            for hotspot1, hotspot2, similarity in similarity_list:
                print(f"  {hotspot1['function_name']} ({file1}) vs {hotspot2['function_name']} ({file2}) - Similarity: {similarity:.4f}")
