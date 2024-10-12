import os
import sqlite3
import json
import tabulate as tb

class DatabaseManager:
    
    def create_db(self):
        # Get the path of the current directory
        current_directory = os.path.dirname(os.path.abspath(__file__))
        print("Database created in", current_directory)
        # Full path of the database in the current directory
        db_path = os.path.join(current_directory, 'disassembly_info.db')
    
        # Check if the database file already exists
        if os.path.exists(db_path):
            print("Existing database found. Deleting...")
            os.remove(db_path)
    
        # Create the database and table if they don't already exist
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Create the main 'info' table
        c.execute('''CREATE TABLE IF NOT EXISTS info
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, namef TEXT, 
                    libreria TEXT, versione_libreria TEXT, compilatore TEXT, 
                    versione_compilatore TEXT, architettura TEXT, filetype TEXT, call_graph TEXT)''')
        # Create the additional 'function_info' table
        c.execute('''CREATE TABLE IF NOT EXISTS function_info
                    (function_id INTEGER PRIMARY KEY AUTOINCREMENT, filename_id INTEGER,
                    function_name TEXT, entry_point TEXT, address TEXT, assembly_code TEXT, 
                    bytecodes TEXT, bfs_result TEXT, dfs_result TEXT,
                    FOREIGN KEY(filename_id) REFERENCES info(id))''')
        conn.commit()
        conn.close()


    def save_to_db(self, filename, namef, libreria, versione_libreria, compilatore, versione_compilatore, architettura, filetype, functions_info_checked, call_graph):
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disassembly_info.db'))
        c = conn.cursor()
        c.execute('''INSERT INTO info (filename, namef, libreria, 
                    versione_libreria, compilatore, versione_compilatore, architettura, filetype, call_graph) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (filename, namef, libreria, versione_libreria, compilatore, 
                    versione_compilatore, architettura, filetype, json.dumps(call_graph)))
        last_row_id = c.lastrowid
    
        # Saving function information into the database
        for function_info in functions_info_checked:
            assembly_code_str = "\n".join(function_info[3])  # Convert the list of instructions into a string
            assembly_code_str_cleaned = assembly_code_str.replace("\n", "  ")  # Remove newline characters
            bytecodes_str = "\n".join(function_info[4])  # Convert the list of bytecodes into a string
            bytecodes_str_cleaned = bytecodes_str.replace("\n", "  ")  # Remove newline characters
            address_str = "\n".join(function_info[2])  # It is not necessary to convert if it's already a string
            address_str_cleaned = address_str.replace("\n", "  ")  # Remove newline characters
            c.execute('''INSERT INTO function_info (filename_id, function_name, entry_point, address, assembly_code, bytecodes, bfs_result, dfs_result) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (last_row_id, function_info[0], function_info[1], address_str_cleaned, assembly_code_str_cleaned, bytecodes_str_cleaned, function_info[5], function_info[6]))

        conn.commit()
        conn.close()
        

    def print_db_info(self):
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disassembly_info.db'))
        c = conn.cursor()
    
        c.execute('''SELECT * FROM info''')
        rows = c.fetchall()
    
        for row in rows:
            print("Binary file name =", row[2])
            print("Binary file path =", row[1])
            print("Library name =", row[3])
            print("Library version =", row[4])
            print("Compiler name =", row[5])
            print("Compiler version =", row[6])
            print("Architecture on which the file was compiled =", row[7])
            print("File type =", row[8])
            print("Call graph =", json.loads(row[9]))
    
            filename_id = row[0]  # Get the ID of the file
            print("\nFunction Info:")
            # Retrieve function information related to this file.
            c.execute('''SELECT * FROM function_info WHERE filename_id = ?''', (filename_id,))
            function_rows = c.fetchall()
            for function_row in function_rows:
                print("\nName function =", function_row[2])
                print("Function entry point =", function_row[3])
                print("Address =", function_row[4])  # Address added
                print("Assembly Code:", function_row[5])
                print("Bytecodes:", function_row[6])  
                bfs_result = function_row[7]  
                dfs_result = function_row[8] 
                if not bfs_result or bfs_result == "":
                    print("BFS Result is empty or NULL or empty string")
                else:
                    try:
                        print("BFS Result:", json.loads(bfs_result))
                    except json.JSONDecodeError as e:
                        #print("Error decoding BFS Result as JSON:", e)
                        print("BFS result []")
    
                if not dfs_result or dfs_result == "":
                    print("DFS Result is empty or NULL or empty string")
                else:
                    try:
                        print("DFS Result:", json.loads(dfs_result))
                    except json.JSONDecodeError as e:
                        #print("Error decoding DFS Result as JSON:", e)
                        print("DFS result []")
    
        conn.close()

    def print_db_final(self):
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disassembly_info.db'))
        c = conn.cursor()

        c.execute('''SELECT * FROM info''')
        rows = c.fetchall()

        for row in rows:
            call_graph = self.format_call_graph(row[9])

            binary_table_data = [
                ["Binary file name", row[2]],
                ["Binary file path", row[1]],
                ["Library name", row[3]],
                ["Library version", row[4]],
                ["Compiler name", row[5]],
                ["Compiler version", row[6]],
                ["Architecture", row[7]],
                ["File type", row[8]],
                ["Call graph", call_graph],
            ]

            print(tb.tabulate(binary_table_data, headers=["", ""], tablefmt="grid"))

            filename_id = row[0]  # Get the ID of the file
            print("\nFunction Info:")

            c.execute('''SELECT * FROM function_info WHERE filename_id = ?''', (filename_id,))
            function_rows = c.fetchall()

            headers = ["Name function", "Function entry point", "Address", "Assembly Code", "Bytecodes", "BFS Result", "DFS Result"]
            table_data = []
            for function_row in function_rows:
                assembly_code_lines = function_row[5].split("  ")
                formatted_assembly_code = "\n".join(assembly_code_lines)

                bytecodes_lines = function_row[6].split("  ")
                formatted_bytecodes = "\n".join(bytecodes_lines)

                # Format address with newline after double space
                address_lines = function_row[4].split("  ")
                formatted_address = "\n".join(address_lines)

                bfs_result = function_row[7]
                dfs_result = function_row[8]

                row_data = [
                    function_row[2],  # Name function
                    function_row[3],  # Function entry point
                    formatted_address,  # Address with newline after double space
                    formatted_assembly_code,  # Assembly Code
                    formatted_bytecodes,  # Bytecodes
                    self.format_result(bfs_result),  # BFS Result
                    self.format_result(dfs_result),  # DFS Result
                ]

                table_data.append(row_data)

            print(tb.tabulate(table_data, headers=headers, tablefmt="grid"))

        conn.close()

    def format_call_graph(self, call_graph):
        if not call_graph:
            return "[]"
        try:
            parts = call_graph.split(" - ")
            formatted_call_graph = ""
            count = 0
            for part in parts:
                formatted_call_graph += part
                count += 1
                if count % 3 == 0:  # Added control for the third character “-”
                    formatted_call_graph += "\n"
                else:
                    formatted_call_graph += " - "  # We keep the space “-” between the blocks.
            return formatted_call_graph.strip()  # Remove any trailing spaces
        except Exception as e:
            return "[]"

    def format_result(self, result):
        if not result:
            return "[]"
        try:
            result_list = json.loads(result)
            result_str = ', '.join(map(str, result_list))  # Convert elements to string if they are not
            # Divide the string into lines of up to 30 characters.
            result_lines = [result_str[i:i+30] for i in range(0, len(result_str), 30)]
            return '\n'.join(result_lines)
        except json.JSONDecodeError:
            return "[]"
