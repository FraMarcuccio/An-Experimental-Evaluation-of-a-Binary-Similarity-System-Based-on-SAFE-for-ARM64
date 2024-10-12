# analysis.py

import os
import sqlite3
import json
import numpy as np
import tensorflow as tf
from capstone import *
from capstone.arm64 import *

class DatabaseFunctionAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_functions_info_from_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        functions_info = []

        c.execute('''SELECT * FROM info''')
        rows = c.fetchall()

        for row in rows:
            filename = row[2]
            functions_info_per_file = []

            filename_id = row[0]
            c.execute('''SELECT * FROM function_info WHERE filename_id = ?''', (filename_id,))
            function_rows = c.fetchall()
            for function_row in function_rows:
                function_data = {
                    "function_name": function_row[2],
                    "entry_point": function_row[3],
                    "address": function_row[4],
                    "assembly_code": function_row[5],
                    "bytecodes": function_row[6],
                }
                bfs_result = function_row[7]
                dfs_result = function_row[8]
                if bfs_result and bfs_result != "":
                    try:
                        function_data["bfs_result"] = json.loads(bfs_result)
                    except json.JSONDecodeError:
                        function_data["bfs_result"] = []

                if dfs_result and dfs_result != "":
                    try:
                        function_data["dfs_result"] = json.loads(dfs_result)
                    except json.JSONDecodeError:
                        function_data["dfs_result"] = []

                functions_info_per_file.append(function_data)

            functions_info.append({
                "binary_file_name": filename,
                "functions": functions_info_per_file
            })

        conn.close()
        return functions_info

    @staticmethod
    def filter_reg(op):
        return op["value"]

    @staticmethod
    def filter_imm(op):
        imm_str = op["value"].replace('#', '')
        try:
            imm = int(imm_str, 0)
            if -5000 <= imm <= 5000:
                return hex(imm)
            else:
                return 'HIMM'
        except ValueError:
            return 'HIMM'

    @staticmethod
    def filter_mem(op):
        base = op.get("base", "0")
        disp = op.get("disp", "0")
        scale = op.get("scale", "1")
        mem_str = f"[{base}*{scale}+{disp}]"
        return mem_str.replace('0*1+0', 'MEM')

    @staticmethod
    def filter_memory_references(instruction):
        inst = instruction["mnemonic"]
        operands = instruction["operands"]

        for op in operands:
            if op["type"] == 'reg':
                inst += " " + DatabaseFunctionAnalyzer.filter_reg(op)
            elif op["type"] == 'imm':
                inst += " " + DatabaseFunctionAnalyzer.filter_imm(op)
            elif op["type"] == 'mem':
                inst += DatabaseFunctionAnalyzer.filter_mem(op)
            inst += ","

        inst = inst.rstrip(',')
        inst = inst.replace(" ", "_")

        return "A_" + inst

    def analyze(self, instructions):
        result = []
        for instruction in instructions:
            mnemonic = instruction.mnemonic
            operands = []
            op_str = instruction.op_str
            inside_mem = False
            current_op = ''

            for char in op_str:
                if char == '[':
                    inside_mem = True
                if char == ']':
                    inside_mem = False

                if char == ',' and not inside_mem:
                    operands.append(current_op.strip())
                    current_op = ''
                else:
                    current_op += char

            if current_op:
                operands.append(current_op.strip())

            parsed_operands = []
            for operand in operands:
                if operand.startswith('x') or operand.startswith('w') or operand.startswith('sp') or operand.startswith('fp') or operand.startswith('lr'):
                    parsed_operands.append({"type": 'reg', "value": operand})
                elif operand.startswith('#'):
                    parsed_operands.append({"type": 'imm', "value": operand})
                elif '[' in operand and ']' in operand:
                    base_disp = operand.strip('[]').split(',')
                    base = base_disp[0].strip()
                    disp = base_disp[1].strip().replace('#', '') if len(base_disp) > 1 else '0'
                    parsed_operands.append({"type": 'mem', "base": base, "disp": disp})
                else:
                    parsed_operands.append({"type": 'unknown', "value": operand})

            instruction_dict = {
                'mnemonic': mnemonic,
                'operands': parsed_operands
            }
            filtered_instruction = self.filter_memory_references(instruction_dict)
            result.append(filtered_instruction)

        return result


class InstructionsConverter:
    def __init__(self, json_i2id):
        if not os.path.isfile(json_i2id):
            raise ValueError(f"Il file {json_i2id} non esiste.")
        
        try:
            with open(json_i2id, 'r') as f:
                self.i2id = json.load(f)
        except IOError as e:
            raise ValueError(f"Errore nell'apertura del file {json_i2id}: {e}")

    def convert_to_ids(self, instructions_list):
        ret_array = []
        for x in instructions_list:
            if x in self.i2id:
                ret_array.append(self.i2id[x] + 1)
            elif 'X_' in x:
                ret_array.append(self.i2id['X_UNK'] + 1)
            elif 'A_' in x:
                ret_array.append(self.i2id['A_UNK'] + 1)
            elif 'M_' in x:
                ret_array.append(self.i2id['M_UNK'] + 1)
            else:
                ret_array.append(self.i2id['X_UNK'] + 1)
        return ret_array


class FunctionNormalizer:
    def __init__(self, max_instruction):
        self.max_instructions = max_instruction

    def normalize(self, f):
        f = np.asarray(f[0:self.max_instructions])
        length = f.shape[0]
        if f.shape[0] < self.max_instructions:
            f = np.pad(f, (0, self.max_instructions - f.shape[0]), mode='constant')
        return f, length

    def normalize_function_pairs(self, pairs):
        lengths = []
        new_pairs = []
        for x in pairs:
            f0, len0 = self.normalize(x[0])
            f1, len1 = self.normalize(x[1])
            lengths.append((len0, len1))
            new_pairs.append((f0, f1))
        return new_pairs, lengths

    def normalize_functions(self, functions):
        lengths = []
        new_functions = []
        for f in functions:
            f, length = self.normalize(f)
            lengths.append(length)
            new_functions.append(f)
        return new_functions, lengths


class SAFEEmbedder:
    def __init__(self, model_file):
        self.model_file = model_file
        self.graph = tf.Graph()  # Create a new TensorFlow graph.
        self.session = None
        self.x_1 = None
        self.len_1 = None
        self.emb = None

    def loadmodel(self):
        with self.graph.as_default():  # Use the new graph as the default graph.
            with tf.io.gfile.GFile(self.model_file, "rb") as f:
                graph_def = tf.compat.v1.GraphDef()
                graph_def.ParseFromString(f.read())
                tf.import_graph_def(graph_def)
                self.session = tf.compat.v1.Session(graph=self.graph)  # Create the session using the new graph
        return self.session

    def get_tensor(self):
        with self.graph.as_default():  # Use the new graph as the default graph.
            self.x_1 = self.session.graph.get_tensor_by_name("import/x_1:0")
            self.len_1 = self.session.graph.get_tensor_by_name("import/lengths_1:0")
            self.emb = tf.nn.l2_normalize(self.session.graph.get_tensor_by_name('import/Embedding1/dense/BiasAdd:0'), axis=1)

    def embedd(self, nodi_input, lengths_input):
        with self.graph.as_default():  # Use the new graph as the default graph.
            out_embedding = self.session.run(self.emb, feed_dict={
                self.x_1: nodi_input,
                self.len_1: lengths_input
            })
        return out_embedding
