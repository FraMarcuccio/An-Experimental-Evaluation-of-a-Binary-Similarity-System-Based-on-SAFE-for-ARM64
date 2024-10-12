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

class GraphHandler:

    def build_graph(call_graph, functions):
        G = nx.DiGraph()

        if not isinstance(call_graph, dict):
            return G

        for source, destinations in call_graph.items():
            G.add_node(source)

        for source, destinations in call_graph.items():
            for destination in destinations:
                if source and destination:
                    try:
                        source_int = int(source, 16)
                        destination_int = int(destination, 16)
                        offset = destination_int - source_int
                        G.add_edge(source, destination, offset=offset)
                    except ValueError:
                        print(f"Error converting address: source={source}, destination={destination}")
        return G

    def build_function_graph(call_graph, functions):
        G = nx.DiGraph()

        function_dict = {func['entry_point']: func for func in functions}

        for entry_point, func in function_dict.items():
            G.add_node(entry_point, function_name=func['function_name'])

        for source, destinations in call_graph.items():
            for destination in destinations:
                if source in function_dict and destination in function_dict:
                    source_name = function_dict[source]['function_name']
                    destination_name = function_dict[destination]['function_name']
                    try:
                        source_int = int(source, 16)
                        destination_int = int(destination, 16)
                        offset = destination_int - source_int
                        G.add_edge(source_name, destination_name, offset=offset)
                    except ValueError:
                        print(f"Error converting address: source={source}, destination={destination}")
        return G

    def print_call_graph(call_graph, functions):
        function_dict = {func['entry_point']: func['function_name'] for func in functions}
        for source, destinations in call_graph.items():
            for destination in destinations:
                if source in function_dict and destination in function_dict:
                    source_name = function_dict[source]
                    dest_name = function_dict[destination]
                    print(f"{source_name} -> {dest_name}")

    def compute_left_connected_components(call_graph, functions):
        G = nx.Graph()

        if not isinstance(call_graph, dict):
            return []

        nodes = [(func['entry_point'], {"function_name": func['function_name'], "id": func['function_id']}) for func in functions]
        edges = [(source.strip(), destination.strip()) for source, destinations in call_graph.items() for destination in destinations]

        addresses = set(node[0] for node in nodes)
        edges = [(source, destination) for source, destination in edges if source in addresses and destination in addresses]

        G.add_nodes_from(nodes)
        G.add_edges_from(edges)

        component_sizes = [len(comp) for comp in sorted(nx.connected_components(G), key=len, reverse=True)]

        return component_sizes

    @staticmethod
    def normalize_component_size_similarity(sizes1, sizes2):
        # Normalize the lists by dividing by the total sum
        total_size1 = sum(sizes1)
        total_size2 = sum(sizes2)
        
        if total_size1 > 0:
            norm_sizes1 = [size / total_size1 for size in sizes1]
        else:
            norm_sizes1 = sizes1
        
        if total_size2 > 0:
            norm_sizes2 = [size / total_size2 for size in sizes2]
        else:
            norm_sizes2 = sizes2
        
        # Align the lists by length, adding zeros where necessary
        max_len = max(len(norm_sizes1), len(norm_sizes2))
        norm_sizes1 = np.pad(norm_sizes1, (0, max_len - len(norm_sizes1)), 'constant')
        norm_sizes2 = np.pad(norm_sizes2, (0, max_len - len(norm_sizes2)), 'constant')
        
        # Calculate the Euclidean distance between the two normalized lists
        euclidean_distance = np.linalg.norm(np.array(norm_sizes1) - np.array(norm_sizes2))
        
        # Convert the distance into a similarity
        similarity = 1 / (1 + euclidean_distance)
        
        return similarity

    @staticmethod
    def compute_number_of_components_similarity(num_components1, num_components2):
        # Calculate the Jaccard similarity for the number of components
        set_num1 = {num_components1}
        set_num2 = {num_components2}

        intersection = len(set_num1.intersection(set_num2))
        union = len(set_num1.union(set_num2))

        jaccard_similarity = intersection / union if union != 0 else 0.0

        return jaccard_similarity

    @staticmethod
    def combined_similarity(sizes1, sizes2, jaccard_weight=0.5, euclidean_weight=0.5):
        # Similarity between the component sizes using Euclidean distance
        num_components1 = len(sizes1)
        num_components2 = len(sizes2)
        number_similarity = GraphHandler.compute_number_of_components_similarity(num_components1, num_components2)
        
        # Similarity between the component sizes using Euclidean distance
        size_similarity = GraphHandler.normalize_component_size_similarity(sizes1, sizes2)
        
        # Combine the Jaccard similarity and the Euclidean similarity with weights
        combined_similarity = (jaccard_weight * number_similarity) + (euclidean_weight * size_similarity)
        
        return combined_similarity
