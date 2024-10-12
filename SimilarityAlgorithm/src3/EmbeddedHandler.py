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

class EmbeddedHandler:
        
    def generate_function_key(function):
        #return (function['function_name'], function['entry_point'])
        return function['function_name']

    def calculate_embeddeds(data, db_path):
        db_analyzer = DatabaseFunctionAnalyzer(db_path)
        functions_info = db_analyzer.get_functions_info_from_db()

        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        md.detail = True

        json_i2id_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'word2id.json')
        converter = InstructionsConverter(json_i2id_path)

        normalizer = FunctionNormalizer(max_instruction=150)
        embedder = SAFEEmbedder(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'safe_aarch64.pb'))
        embedder.loadmodel()
        embedder.get_tensor()

        embeddings_with_ids = {}

        for entry in data['info']:
            for function_info in entry['functions']:
                function_name = function_info['function_name']
                bytecode_string = function_info['bytecodes']
                entry_point = int(function_info['entry_point'].replace("0x", ""), 16)
                address = entry_point

                bytecode = bytes.fromhex(bytecode_string)
                instructions = list(md.disasm(bytecode, address))

                result = db_analyzer.analyze(instructions)

                flattened_instructions = [instr for instr in result]
                converted_instructions = converter.convert_to_ids(flattened_instructions)

                normalized_instructions, lengths = normalizer.normalize_functions([converted_instructions])

                embedding = embedder.embedd(normalized_instructions, lengths)

                function_key = EmbeddedHandler.generate_function_key(function_info)
                embeddings_with_ids[function_key] = embedding[0].tolist()

        for info_entry in data['info']:
            for function in info_entry['functions']:
                function_key = EmbeddedHandler.generate_function_key(function)
                if function_key in embeddings_with_ids:
                    function['embeddeds'] = embeddings_with_ids[function_key]

        return data

    def extract_and_calculate_fuzzy_similarity_mean(fuzzy_matches):
        similarities = []
        for item in fuzzy_matches:
            if isinstance(item, tuple) and len(item) == 3:
                _, _, similarity = item
                if isinstance(similarity, (int, float)):
                    similarities.append(similarity)
        if not similarities:
            print("Fuzzy matches list is empty or has invalid values.")
        return np.mean(similarities) if similarities else 0.0

    def extract_and_calculate_embedding_similarity_mean(embedding_comparisons):
        similarities = []
        for item in embedding_comparisons:
            if isinstance(item, tuple) and len(item) == 2:
                _, similarity = item
                if isinstance(similarity, (int, float, np.ndarray)):
                    if isinstance(similarity, np.ndarray):
                        similarity = similarity.item()  # Convert array to scalar
                    similarities.append(similarity)
        if not similarities:
            print("Embedding comparisons list is empty or has invalid values.")
        return np.mean(similarities) if similarities else 0.0
