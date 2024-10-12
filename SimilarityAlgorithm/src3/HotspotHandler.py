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

class HotspotHandler:

    def find_hotspot(database):
        hotspot_data = {}

        for entry in database['info']:
            call_graph = entry['call_graph']
            functions = entry['functions']

            # Dajeee graph
            G = nx.DiGraph()

            for source, destinations in call_graph.items():
                for destination in destinations:
                    if source and destination:
                        try:
                            source_int = int(source, 16)
                            destination_int = int(destination, 16)
                            G.add_edge(source, destination)
                        except ValueError:
                            print(f"Error converting address: source={source}, destination={destination}")

            for func in functions:
                entry_point = func['entry_point']
                if entry_point in G:
                    predecessors = list(G.predecessors(entry_point))
                    successors = list(G.successors(entry_point))
                    degree = len(predecessors) + len(successors)

                    # Calculate the overall degree of predecessors and successors
                    predecessor_degrees = sum(len(list(G.predecessors(pred))) + len(list(G.successors(pred))) for pred in predecessors)
                    successor_degrees = sum(len(list(G.predecessors(succ))) + len(list(G.successors(succ))) for succ in successors)
                    total_connected_degree = predecessor_degrees + successor_degrees

                    if degree > 1:  # If the function has more than one predecessor or successor
                        if entry['filename'] not in hotspot_data:
                            hotspot_data[entry['filename']] = []

                        hotspot_data[entry['filename']].append({
                            'function_name': func['function_name'],
                            'entry_point': entry_point,
                            'degree': degree,
                            'predecessor_degrees': predecessor_degrees,
                            'successor_degrees': successor_degrees,
                            'total_connected_degree': total_connected_degree,
                            'predecessors': predecessors,
                            'successors': successors
                        })
                    else:
                        #print(f"Warning: Entry point {entry_point} not found in graph nodes")
                        pass
                    
        return hotspot_data

    def calculate_hotspot_similarity(hotspots1, hotspots2):
        if not hotspots1 or not hotspots2:
            print("Empty hotspots1 or hotspots2")
            return [], 0

        similarity_list = []

        for hotspot1 in hotspots1:
            for hotspot2 in hotspots2:
                similarity = 0

                # Weighting of various factors, all of these are chosen by me
                name_weight = 0.4
                degree_weight = 0.2
                connected_degree_weight = 0.1
                pred_succ_weight = 0.1
                entry_point_weight = 0.2  # Addition of a specific weight for the entry point

                # 1. Compare function names
                if hotspot1['function_name'] == hotspot2['function_name']:
                    similarity += name_weight

                    # 2. Compare entry points
                    if hotspot1['entry_point'] == hotspot2['entry_point']:
                        similarity += entry_point_weight

                    # 3. Compare degrees
                    degree_diff = abs(hotspot1['degree'] - hotspot2['degree'])
                    similarity += degree_weight * (1 - degree_diff / max(hotspot1['degree'], hotspot2['degree'], 1))

                    # 4. Compare total degrees
                    connected_degree_diff = abs(hotspot1['total_connected_degree'] - hotspot2['total_connected_degree'])
                    similarity += connected_degree_weight * (1 - connected_degree_diff / max(hotspot1['total_connected_degree'], hotspot2['total_connected_degree'], 1))

                    # 5. Compare predecessors and successors
                    common_predecessors = set(hotspot1['predecessors']) & set(hotspot2['predecessors'])
                    common_successors = set(hotspot1['successors']) & set(hotspot2['successors'])

                    # Take the percentage of common predecessors and successors
                    if len(hotspot1['predecessors']) > 0:
                        similarity += pred_succ_weight * (len(common_predecessors) / len(hotspot1['predecessors']))
                    if len(hotspot1['successors']) > 0:
                        similarity += pred_succ_weight * (len(common_successors) / len(hotspot1['successors']))

                else:
                    # If the names do not match, the similarity is very low
                    similarity = 0.1

                # Ensure similarity does not exceed 1
                similarity = min(similarity, 1.0)

                similarity_list.append((hotspot1, hotspot2, similarity))

        similarity_list.sort(key=lambda x: x[2], reverse=True)

        avg_similarity = np.mean([sim[2] for sim in similarity_list]) if similarity_list else 0
        return similarity_list, avg_similarity

    # Function to compare hotspots between two datasets
    def compare_hotspots(hotspot_data1, hotspot_data2):
        comparisons = []

        for file1, hotspots1 in hotspot_data1.items():
            for file2, hotspots2 in hotspot_data2.items():
                similarity_list, avg_similarity = HotspotHandler.calculate_hotspot_similarity(hotspots1, hotspots2)
                comparisons.append((file1, file2, similarity_list, avg_similarity))

        comparisons.sort(key=lambda x: x[3], reverse=True)  # Sort by average similarity
        return comparisons

    # Calculate overall similarity between two hotspot datasets
    def calculate_overall_similarity(hotspot_comparison_result):
        high_similarity_threshold = 0.8  # Threshold to consider a hotspot as highly similar
        total_hotspots = 0
        high_similarity_count = 0

        for comparison in hotspot_comparison_result:
            _, _, similarity_list, _ = comparison
            total_hotspots += len(similarity_list)
            high_similarity_count += sum(1 for _, _, similarity in similarity_list if similarity >= high_similarity_threshold)

        overall_similarity = high_similarity_count / total_hotspots if total_hotspots > 0 else 0
        return overall_similarity
