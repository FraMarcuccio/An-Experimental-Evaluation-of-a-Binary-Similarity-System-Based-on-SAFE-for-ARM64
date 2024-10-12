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
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import confusion_matrix
from node2vec import Node2Vec
from networkx.algorithms.similarity import graph_edit_distance
import seaborn as sns
import matplotlib.pyplot as plt
import re

from DatabaseHandler import DatabaseHandler
from GraphHandler import GraphHandler
from BinaryHandler import BinaryHandler
from HotspotHandler import HotspotHandler
from EmbeddedHandler import EmbeddedHandler
from OutputHandler import OutputPrinter
from MetricsHandler import MetricsHandler

def generate_function_key(function):
    #return (function['function_name'], function['entry_point'])
    return function['function_name']

def compare_binary_files_and_functions(data1, data2):
    all_comparisons = []

    for entry1 in data1['info']:
        print(f"File from db1: {entry1['filename']}")

        call_graph = entry1['call_graph']
        graph = GraphHandler.build_graph(call_graph, entry1['functions'])
        function_graph = GraphHandler.build_function_graph(call_graph, entry1['functions'])
        component_sizes = GraphHandler.compute_left_connected_components(call_graph, entry1['functions'])

        print("Call Graph:")
        GraphHandler.print_call_graph(call_graph, entry1['functions'])

        print("Graph Nodes:")
        pprint.pprint(graph.nodes(data=True))
        print("Graph Edges:")
        pprint.pprint(graph.edges(data=True))

        print("Function Graph:")
        pprint.pprint(function_graph.nodes(data=True))
        print("Function Graph Edges:")
        pprint.pprint(function_graph.edges(data=True))

        print("Connected Component Sizes:")
        pprint.pprint(component_sizes)
        print("-" * 40)

        for entry2 in data2['info']:
            print(f"Comparing file from db1: {entry1['filename']} with file from db2: {entry2['filename']}")

            # Extract and build structures for the first file
            call_graph1 = entry1['call_graph']
            functions1 = {generate_function_key(func): func for func in entry1['functions']}
            component_sizes1 = GraphHandler.compute_left_connected_components(call_graph1, entry1['functions'])

            # Extract and build structures for the second file
            call_graph2 = entry2['call_graph']
            functions2 = {generate_function_key(func): func for func in entry2['functions']}
            component_sizes2 = GraphHandler.compute_left_connected_components(call_graph2, entry2['functions'])

            # Find common and unmatched functions
            common_functions_keys = functions1.keys() & functions2.keys()
            common_functions = [functions1[k] for k in common_functions_keys]
            unmatched_functions1 = [functions1[k] for k in functions1.keys() - common_functions_keys]
            unmatched_functions2 = [functions2[k] for k in functions2.keys() - common_functions_keys]

            embedding_comparisons = []
            max_similarity_common = (None, None, 0)
            weighted_avg_similarity_common = 0.0

            if common_functions:
                embeddings1_common = [(str(i), [functions1[func_key]['embeddeds']]) for i, func_key in enumerate(common_functions_keys)]
                embeddings2_common = [(str(i), [functions2[func_key]['embeddeds']]) for i, func_key in enumerate(common_functions_keys)]
                
                prof_common = PairWiseSimilarity(embeddings1_common, embeddings2_common, None)
                
                # Calculate max similarity for common functions with matrices
                similarity_matrix = np.zeros((len(embeddings1_common), len(embeddings2_common)))
                for i in range(len(embeddings1_common)):
                    for j in range(len(embeddings2_common)):
                        similarity_matrix[i, j] = prof_common._compute_similarity(embeddings1_common[i][1], embeddings2_common[j][1])
                
                best_match = BinaryHandler.find_best_match(similarity_matrix, common_functions, common_functions)
                if best_match:
                    max_similarity_common = best_match
                
                weighted_avg_similarity_common = np.mean(similarity_matrix) if similarity_matrix.size > 0 else 0

                for i, func_key in enumerate(common_functions_keys):
                    embedding1 = embeddings1_common[i][1]
                    embedding2 = embeddings2_common[i][1]
                    similarity = prof_common._compute_similarity(embedding1, embedding2)
                    embedding_comparisons.append((func_key, similarity))

            embeddings1_unmatched = [(func_key, functions1[func_key]['embeddeds']) for func_key in functions1.keys() - common_functions_keys]
            embeddings2_unmatched = [(func_key, functions2[func_key]['embeddeds']) for func_key in functions2.keys() - common_functions_keys]

            fuzzy_matches = []
            max_fuzzy_similarity = (None, None, 0)
            max_fuzzy_match = None
            max_sim_unmatch = None 
            weighted_avg_similarity = 0.0

            if embeddings1_unmatched and embeddings2_unmatched:
                prof_unmatched = PairWiseSimilarity(embeddings1_unmatched, embeddings2_unmatched, None)
                threshold = 0.5  # Similarity threshold to be set as needed
                
                fuzzy_matches, weighted_avg_similarity = BinaryHandler.compute_fuzzy_similarity(prof_unmatched, embeddings1_unmatched, embeddings2_unmatched, threshold)

                similarity_matrix_unmatched = np.zeros((len(embeddings1_unmatched), len(embeddings2_unmatched)))
                for i in range(len(embeddings1_unmatched)):
                    for j in range(len(embeddings2_unmatched)):
                        similarity_matrix_unmatched[i, j] = prof_unmatched._compute_similarity(
                            np.expand_dims(embeddings1_unmatched[i][1], axis=0), 
                            np.expand_dims(embeddings2_unmatched[j][1], axis=0)
                        )
                
                best_match_unmatched, max_sim_unmatched = BinaryHandler.find_best_match_unmatched(similarity_matrix_unmatched, embeddings1_unmatched, embeddings2_unmatched)

                # Verify that both variables have valid values
                if best_match_unmatched is not None and max_sim_unmatched is not None:
                    max_fuzzy_match = best_match_unmatched
                    max_sim_unmatch = max_sim_unmatched
            
            bfs_dfs_similarities_common, bfs_dfs_similarities_unmatched = BinaryHandler.calculate_bfs_dfs_similarities(functions1, functions2)

            all_comparisons.append({
                'file1': entry1['filename'],
                'file2': entry2['filename'],
                'common_functions': common_functions,
                'embedding_comparisons': embedding_comparisons,
                'max_similarity_common': max_similarity_common,
                'fuzzy_matches': fuzzy_matches,
                'weighted_avg_similarity': weighted_avg_similarity,
                'weighted_avg_similarity_common': weighted_avg_similarity_common,
                'component_size_file1': component_sizes1,
                'component_size_file2': component_sizes2,
                'unmatched_functions_file1': unmatched_functions1,
                'unmatched_functions_file2': unmatched_functions2,
                'namef1': entry1['namef'],
                'namef2': entry2['namef'],
                'max_fuzzy_match': max_fuzzy_match,
                'max_sim_unmatch': max_sim_unmatch,
                'bfs_dfs_similarities_common': bfs_dfs_similarities_common,
                'bfs_dfs_similarities_unmatched': bfs_dfs_similarities_unmatched,
            })

    return all_comparisons

if __name__ == "__main__":
    # List of databases to compare with bzoc500.db.
    """
    db_list = [
        'boost1.db',
        'zlib1.db',
        'curl1.db',
        'openssl1.db'
    ]
    """
    db_list = [
        'file_1.db',
        'file_2.db',
        'file_3.db',
        'file_4.db',
        'file_5.db',
        'file_6.db',
        'file_7.db',
        'file_8.db',
        'file_9.db',
        'file_10.db',
        'file_11.db',
        'file_12.db',
        'file_13.db',
        'file_14.db',
        'file_15.db',
        'file_16.db',
        'file_17.db',
        'file_18.db',
        'file_19.db',
        'file_20.db',
        'file_21.db',
        'file_22.db',
        'file_23.db',
        'file_24.db',
        'file_25.db',
        'file_26.db',
        'file_27.db',
        'file_28.db',
        'file_29.db',
        'file_30.db',
        'file_31.db',
        'file_32.db',
        'file_33.db',
        'file_34.db',
        'file_35.db',
        'file_36.db',
        'file_37.db',
        'file_38.db',
        'file_39.db',
        'file_40.db',
        'file_41.db',
        'file_42.db',
        'file_43.db',
        'file_44.db',
        'file_45.db',
        'file_46.db',
        'file_47.db',
        'file_48.db',
        'file_49.db',
        'file_50.db',
    ]
    reference_db = 'bzoc500.db'

    comparison_results = {}
    metrics_results = {}

    for db_path in db_list:
        # Create a DatabaseHandler for each comparison
        db_handler = DatabaseHandler(db_path, reference_db)
        
        # Retrieve and calculate data
        data1 = db_handler.fetch_all_data(db_path)
        data2 = db_handler.fetch_all_data(reference_db)
        
        data1 = EmbeddedHandler.calculate_embeddeds(data1, db_path)
        data2 = EmbeddedHandler.calculate_embeddeds(data2, reference_db)

        # Database comparison
        comparison_result = compare_binary_files_and_functions(data1, data2)
        
        # Store results
        comparison_results_without_normalization = []
        comparison_results_with_normalization = []

        # Calculate and print results for the current comparison
        print(f"\nComparison between {db_path} and {reference_db}:")
        print("--------------------------------------FINAL DATA---------------------------------------")
        for file_info in comparison_result:
            OutputPrinter.print_file_comparison(file_info)

        OutputPrinter.print_top_similar_files(comparison_result)

        # Calculate similarity scores without normalization
        for comparison in comparison_result:
            embedding_comparisons = comparison['embedding_comparisons']
            bfs_dfs_similarities_common = comparison['bfs_dfs_similarities_common']
            fuzzy_matches = comparison['fuzzy_matches']
            bfs_dfs_similarities_unmatched = comparison['bfs_dfs_similarities_unmatched']
            common_functions = comparison['common_functions']
            component_sizes1 = comparison['component_size_file1']
            component_sizes2 = comparison['component_size_file2']

            avg_fuzzy_match = EmbeddedHandler.extract_and_calculate_fuzzy_similarity_mean(fuzzy_matches)
            avg_embedding_similarity = EmbeddedHandler.extract_and_calculate_embedding_similarity_mean(embedding_comparisons)
            left_component_similarity = GraphHandler.combined_similarity(component_sizes1, component_sizes2)

            print(f"Similarity between left component graph {component_sizes1} and {component_sizes2}: {left_component_similarity:.4f}")
            print()
            print("bfs dfs common similarities", bfs_dfs_similarities_common)
            print("uncommond", bfs_dfs_similarities_unmatched)

            final_similarity_common, final_similarity_unmatched = BinaryHandler.calculate_final_similarities(bfs_dfs_similarities_common, bfs_dfs_similarities_unmatched)

            print(f"Final BFS DFS similarity (common functions): {final_similarity_common:.2f}")
            print(f"Final BFS DFS similarity (uncommon functions): {final_similarity_unmatched:.2f}")

            similarity_score = (
                0.5 * avg_embedding_similarity +
                0.1 * len(common_functions) +
                0.05 * avg_fuzzy_match +
                0.05 * left_component_similarity +
                0.05 * final_similarity_common +
                0.05 * final_similarity_unmatched
            )
            
            comparison['similarity_score'] = similarity_score

        # Calcola gli hotspot e confronta
        hotspot_data1 = HotspotHandler.find_hotspot(data1)
        hotspot_data2 = HotspotHandler.find_hotspot(data2)
        
        OutputPrinter.print_hotspots(hotspot_data1, "the first dataset")
        OutputPrinter.print_hotspots(hotspot_data2, "the second dataset")

        hotspot_comparison_result = HotspotHandler.compare_hotspots(hotspot_data1, hotspot_data2)
        OutputPrinter.print_comparison_results(hotspot_comparison_result)

        overall_similarity = HotspotHandler.calculate_overall_similarity(hotspot_comparison_result)
        print(f"\nOverall Normalized Similarity between the two datasets: {overall_similarity:.2f}")

        hotspot_similarity_scores = OutputPrinter.maps_similarity_scores_hotspot(hotspot_comparison_result)

        weight_for_hotspot = 0.20
        for comparison in comparison_result:
            key = f"{comparison['file1']}_{comparison['file2']}"
            hotspot_score = hotspot_similarity_scores.get(key, 0.0)
            comparison['similarity_score'] += weight_for_hotspot * hotspot_score
            print(f"Hotspot Score for {key}: {hotspot_score:.4f}")

        comparison_result.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Store scores without normalization
        for comparison in comparison_result:
            comparison_results_without_normalization.append({
                'file1': comparison['file1'],
                'file2': comparison['file2'],
                'similarity_score': comparison['similarity_score']
            })

        # Print similarity scores without normalization
        print()
        print("--------------------------------------Similarity Scores for All File Pairs (Without Normalization)----------------------------------------------------")
        for comparison in comparison_result:
            print(f"File1: {comparison['file1']}, File2: {comparison['file2']}, Similarity: {comparison['similarity_score']:.4f}")

        # Normalize scores
        scores = [comp['similarity_score'] for comp in comparison_result]
        max_score = max(scores)
        min_score = min(scores)

        for comparison in comparison_result:
            if max_score > min_score:
                comparison['similarity_score_normalized'] = (comparison['similarity_score'] - min_score) / (max_score - min_score)
            else:
                comparison['similarity_score_normalized'] = 0.0

        comparison_result.sort(key=lambda x: x['similarity_score_normalized'], reverse=True)
        
        # Store scores with normalization
        for comparison in comparison_result:
            comparison_results_with_normalization.append({
                'file1': comparison['file1'],
                'file2': comparison['file2'],
                'similarity_score_normalized': comparison['similarity_score_normalized']
            })

        print()
        print("--------------------------------------Similarity Scores for All File Pairs (With Final Normalization)----------------------------------------------------")
        for comparison in comparison_result:
            print(f"File1: {comparison['file1']}, File2: {comparison['file2']}, Similarità: {comparison['similarity_score_normalized']:.4f}")
            filecompared = comparison['file1']
        print("File Name first file ", filecompared)

        # Organize results for comparisonresult.json
        comparison_results[db_path] = {
            'without_normalization': comparison_results_without_normalization,
            'with_normalization': comparison_results_with_normalization
        }

        # Save similarity results in comparisonresult.json
        comparison_filename = 'comparisonresult.json'
        if os.path.exists(comparison_filename):
            with open(comparison_filename, 'r') as json_file:
                existing_results = json.load(json_file)
            existing_results.update(comparison_results)
            with open(comparison_filename, 'w') as json_file:
                json.dump(existing_results, json_file, indent=4)
        else:
            with open(comparison_filename, 'w') as json_file:
                json.dump(comparison_results, json_file, indent=4)

        print(f"The results for the comparison between {db_path} and {reference_db} have been saved in 'comparisonresult.json'.")

        k = 10
        # Calculate precision and recall for all modes
        precision_at_k_with_version, recall_at_k_with_version, file_groups_lib_version = MetricsHandler.calculate_precision_recall_at_k(comparison_result, use_normalized_scores=True, max_k=k, consider_version=True)
        precision_at_k_without_version, recall_at_k_without_version, file_groups_lib = MetricsHandler.calculate_precision_recall_at_k(comparison_result, use_normalized_scores=True, max_k=k, consider_version=False)
        precision_at_k_with_filename, recall_at_k_with_filename, file_groups_filename_lib_version = MetricsHandler.calculate_precision_recall_at_k(comparison_result, use_normalized_scores=True, max_k=k, consider_version=True, consider_filename=True)
        precision_at_k_with_filename_without_version, recall_at_k_with_filename_without_version, file_groups_filename_lib = MetricsHandler.calculate_precision_recall_at_k(comparison_result, use_normalized_scores=True, max_k=k, consider_version=False, consider_filename=True)

        # Organize data into a dictionary to save in JSON
        filecompared = comparison_result[0]['file1']  # Use the first comparison file as a key
        metrics_results[filecompared] = {
            "library_name_version": {
                "relevant_total": file_groups_lib_version,
                "precision": precision_at_k_with_version,
                "recall": recall_at_k_with_version
            },
            "library_name_only": {
                "relevant_total": file_groups_lib,
                "precision": precision_at_k_without_version,
                "recall": recall_at_k_without_version
            },
            "filename_library_name_version": {
                "relevant_total": file_groups_filename_lib_version,
                "precision": precision_at_k_with_filename,
                "recall": recall_at_k_with_filename
            },
            "filename_library_name_only": {
                "relevant_total": file_groups_filename_lib,
                "precision": precision_at_k_with_filename_without_version,
                "recall": recall_at_k_with_filename_without_version
            }
        }

        # Save metric results in metricsresult4files.json
        metrics_filename = 'metricsresult4files.json'
        if os.path.exists(metrics_filename):
            with open(metrics_filename, 'r') as json_file:
                existing_metrics_results = json.load(json_file)
            existing_metrics_results.update(metrics_results)
            with open(metrics_filename, 'w') as json_file:
                json.dump(existing_metrics_results, json_file, indent=4)
        else:
            with open(metrics_filename, 'w') as json_file:
                json.dump(metrics_results, json_file, indent=4)

        print(f"The results for the comparison between {db_path} and {reference_db} have been saved in 'metricsresult.json'.")