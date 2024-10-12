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

class MetricsHandler:

    @staticmethod
    def extract_library_and_version(filename):
        # Regex to extract the library name and version from the filename
        match = re.search(r'/(\w+)-(\d+\.\d+\.\d+)/', filename)
        if match:
            library_name = match.group(1)
            version = match.group(2)
            return library_name, version
        return None, None

    @staticmethod
    def extract_library_name(filename):
        # Regex to extract only the library name
        match = re.search(r'/(\w+)-\d+\.\d+\.\d+/', filename)
        if match:
            library_name = match.group(1)
            return library_name
        return None

    @staticmethod
    def extract_filename(filename):
        # Extracts only the file name from the path
        return filename.split('/')[-1]


    def calculate_precision_recall_at_k(comparison_result, use_normalized_scores=False, max_k=10, consider_version=True, consider_filename=False):
        file_groups = {}

        # Populate the file groups by relevance
        for comparison in comparison_result:
            file1 = comparison['file1']
            file2 = comparison['file2']
            similarity_score = comparison['similarity_score_normalized'] if use_normalized_scores else comparison['similarity_score']

            lib1 = MetricsHandler.extract_library_name(file1)
            lib2 = MetricsHandler.extract_library_name(file2)

            ver1, ver2 = (None, None) if not consider_version else MetricsHandler.extract_library_and_version(file1)[1], MetricsHandler.extract_library_and_version(file2)[1]
            filename1, filename2 = (None, None) if not consider_filename else (file1.split('/')[-1], file2.split('/')[-1])

            if consider_filename and consider_version:
                relevant = (filename1 == filename2) and (lib1 == lib2) and (ver1 == ver2)
            elif consider_filename and not consider_version:
                relevant = (filename1 == filename2) and (lib1 == lib2)
            elif consider_version and not consider_filename:
                relevant = (lib1 == lib2) and (ver1 == ver2)
            else:
                relevant = (lib1 == lib2)

            if file1 not in file_groups:
                file_groups[file1] = {'relevant': 0, 'total': 0}

            if relevant:
                file_groups[file1]['relevant'] += 1

            file_groups[file1]['total'] += 1

        # Debugging: print file groups
        print("File groups:", file_groups)

        total_relevant = sum(group['relevant'] for group in file_groups.values())
        print("total relevant ", total_relevant)

        relevant_total_values = [{'relevant': group['relevant'], 'total': group['total']} for group in file_groups.values()]

        precision_at_k = []
        recall_at_k = []

        # Calculate precision and recall for each k up to max_k
        for k in range(1, max_k + 1):
            relevant_count = 0
            for comparison in comparison_result[:k]:
                file1 = comparison['file1']
                file2 = comparison['file2']

                lib1 = MetricsHandler.extract_library_name(file1)
                lib2 = MetricsHandler.extract_library_name(file2)

                ver1, ver2 = (None, None) if not consider_version else MetricsHandler.extract_library_and_version(file1)[1], MetricsHandler.extract_library_and_version(file2)[1]
                filename1, filename2 = (None, None) if not consider_filename else (file1.split('/')[-1], file2.split('/')[-1])

                if consider_filename and consider_version:
                    relevant = (filename1 == filename2) and (lib1 == lib2) and (ver1 == ver2)
                elif consider_filename and not consider_version:
                    relevant = (filename1 == filename2) and (lib1 == lib2)
                elif consider_version and not consider_filename:
                    relevant = (lib1 == lib2) and (ver1 == ver2)
                else:
                    relevant = (lib1 == lib2)

                if relevant:
                    relevant_count += 1

            precision = (relevant_count / k) * 100 if k > 0 else 0
            recall = (relevant_count / total_relevant) * 100 if total_relevant > 0 else 0

            precision_at_k.append(precision)
            recall_at_k.append(recall)

            # Print for each value of k except max_k
            if k < max_k:
                print(f"Precision at k={k}: {precision_at_k[-1]:.2f}%")
                print(f"Recall at k={k}: {recall_at_k[-1]:.2f}%")

        # Final print for k = max_k
        print(f"Precision at k={max_k}: {precision_at_k[-1]:.2f}%")
        print(f"Recall at k={max_k}: {recall_at_k[-1]:.2f}%")

        return precision_at_k, recall_at_k, relevant_total_values

    # Function to plot combined precision and recall
    def plot_precision_recall_combined(precision, recall, title, max_k=10):
        k_values = list(range(1, max_k + 1))

        plt.plot(k_values, precision, marker='o', label='Precision', color='#1f77b4')
        plt.plot(k_values, recall, marker='s', label='Recall', color='#ff7f0e', linestyle='--')

        plt.xlabel('k')
        plt.ylabel('Value (%)')
        plt.title(title)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)

        # Set the same scale for all charts
        plt.ylim(-5, 105)  # Extend a bit beyond 100 to avoid overlapping with maximum values
        plt.yticks(range(0, 101, 10))  # Tick from 0 to 100 with increments of 10

        # Set X-axis ticks with an increment of 1
        plt.xticks(k_values)  # Values of k (1, 2, 3, ..., max_k)
