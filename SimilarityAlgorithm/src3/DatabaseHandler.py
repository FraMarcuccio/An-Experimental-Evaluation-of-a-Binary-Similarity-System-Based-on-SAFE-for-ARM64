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

class DatabaseHandler:
    def __init__(self, db_name1, db_name2):
        self.db_path1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name1)
        self.db_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name2)

    def fetch_all_data(self, db_path):
        data = {}
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute('''SELECT * FROM info''')
        info_rows = c.fetchall()

        data['info'] = []
        for row in info_rows:
            entry = {
                'id': row[0],
                'filename': row[1],
                'namef': row[2],
                'libreria': row[3],
                'versione_libreria': row[4],
                'compilatore': row[5],
                'versione_compilatore': row[6],
                'architettura': row[7],
                'filetype': row[8],
                'call_graph': self._parse_call_graph(row[9]),
                'functions': []
            }
            data['info'].append(entry)

        c.execute('''SELECT * FROM function_info''')
        function_rows = c.fetchall()

        for function_row in function_rows:
            function_entry = {
                'function_id': function_row[0],
                'filename_id': function_row[1],
                'function_name': function_row[2],
                'entry_point': function_row[3],
                'address': function_row[4],
                'assembly_code': function_row[5],
                'bytecodes': function_row[6],
                'bfs_result': self._parse_json(function_row[7]),
                'dfs_result': self._parse_json(function_row[8]),
                'embeddeds': []
            }

            for info_entry in data['info']:
                if info_entry['id'] == function_row[1]:
                    info_entry['functions'].append(function_entry)
                    break

        conn.close()
        return data

    def _parse_json(self, json_str):
        if not json_str or json_str.strip() == "":
            return {}
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}

    def _parse_call_graph(self, call_graph_str):
        if not call_graph_str or call_graph_str.strip() == "NULL":
            return {}
        try:
            call_graph = {}
            edges = call_graph_str.split(' - ')
            for edge in edges:
                if '->' in edge:
                    source, destination = edge.split(' -> ')
                    source = source.strip().strip('"')
                    destination = destination.strip().strip('"')
                    if source in call_graph:
                        call_graph[source].append(destination)
                    else:
                        call_graph[source] = [destination]
            return call_graph
        except Exception as e:
            print(f"Error parsing call graph: {e}")
            return {}
