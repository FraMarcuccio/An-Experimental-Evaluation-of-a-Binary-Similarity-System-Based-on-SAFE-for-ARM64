import os
import shutil
from GhidraDisassembler import GhidraFunctionAnalyzer
from FileManager import FileManager
from DatabaseManager import DatabaseManager
from GraphManager import GraphManager
import networkx as nx
import json

def main():

    graph = GraphManager()
    db_manager = DatabaseManager()
    db_manager.create_db()

    # FILE MANAGER --------------------------------
    file_manager = FileManager()
    
    print(file_manager.ARM_folder)
    architecture = file_manager.last_folder # ARM
    all_files = file_manager.find_files_in_path(file_manager.ARM_folder)
    
    # Initialize a counter to track the number of analyzed files
    file_count = 0
    total_files = len(all_files)  # Total number of files to analyze

    for file in all_files:
        # Increment the counter
        file_count += 1
        print(f"Analyzing file #{file_count} of {total_files}...")

        filename = file
        file_info = file_manager.decompose_path(file)
        namef = file_info["File name"]
        library = file_info["Library"]
        library_version = file_info["Library version"]
        compiler = file_info["Compiler"]
        compiler_version = file_info["Compiler version"]
        optimization = file_info["Optimization"]
        print(f"File path: {namef} from library {library}, version {library_version}")

        # Project pathway
        projects_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project")

        # Remove files and folders from the 'project' folder if present
        file_manager.clear_project_folder(projects_path)

        # GHIDRA BRIDGE -------------------------
        ghidra_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghidra_11.0.1_PUBLIC")
        project_name = "disassembled"
        print("Project created", project_name)
        server_port = 4768
        ghidra_scripts_root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghidra_scripts")
        ghidra_script = "ghidra_bridge_server.py"

        analyzer = GhidraFunctionAnalyzer(ghidra_path, filename, projects_path, project_name, server_port, ghidra_scripts_root_path, ghidra_script)

        # Print file information such as compiler, libraries, versions, etc.
        print("Binary file name:", namef)
        ghidra_filename = analyzer.get_file_name()
        print("File name returned by Ghidra:", ghidra_filename) # This name should match the binary file name
        print("Binary file path:", filename)
        print("Library name:", library)
        print("Library version:", library_version)
        print("Compiler name:", compiler)
        print("Compiler version:", compiler_version)
        print("Architecture the file was compiled on:", architecture)

        # Print the file type, ELF or OBJ
        filetype = analyzer.get_file_type(filename)
        if filetype:
            print("File type:", filetype)
        else:
            print("Unable to get the file type.")
            filetype = "NULL"
        
        print("Calling the graph function\n")
        functions, call_graph = analyzer.get_call_graph()

        # Print function information
        print("Functions:")
        functions_info = []
        
        for function in functions:
            print(f" - Name: {function[0]} (Mangled: {function[1]}) - Entry Point: 0x{function[2]:x}")
            print("Function entry point:", hex(function[2]))

            # Assembly code and other gathered information
            assembly_code, address, bytecodes, last_address = analyzer.get_assembly_functions_ret_stop(str(hex(function[2])))

            # Convert last_address from generic ghidra address format to string
            last_address_str = analyzer.extract_address(last_address)
            print("Last address converted to string:", last_address_str)
            print(type(last_address_str))

            print(f" ------------------------- Entry point: {(str(hex(function[2])))}")
            analyzer.print_blocks_function(str(hex(function[2])))

            initialblock = analyzer.get_first_function_block(str(hex(function[2])))
            print("Initial block object:", initialblock)

            result = analyzer.CFG_and_destinationblocks_ricorsiva(str(hex(function[2])), last_address_str)
            print("Content of result:")
            for block, destinations in result.items():
                print(f"Block: {block}, Type: {type(block)}, Destinations: {destinations}, Type of destinations: {type(destinations)}")

            # NETWORKX MANAGER-----------------
            G = graph.create_undirected_graph(result) # Create an undirected graph
            
            entry_point = str(hex(function[2])).replace('x', '0')
            print("\nEntry point:", entry_point)
            start_node = None
            for block, destinations in result.items():
                if block == entry_point:
                    start_node = block
                    break
            
            if start_node is None:
                print("Entry point not found in the result dictionary.")
            else:
                print("Start node:", start_node)

            print("Start node-----", start_node)
            bfs_result = graph.bfs(G, start_node)
            print("BFS traversal:", bfs_result)

            dfs_result = graph.dfs(G, start_node)
            print("DFS traversal:", dfs_result)

            start_node_str = analyzer.extract_address(start_node)
            print("Start node as string:", start_node_str)
            print(type(start_node_str))
            print("Last address as string", last_address_str)
          
            bfs_filtered = analyzer.confronta_blocchi(bfs_result, last_address_str, start_node_str)
            print("Filtered BFS blocks:", bfs_filtered)

            dfs_filtered = analyzer.confronta_blocchi(dfs_result, last_address_str, start_node_str)
            print("Filtered DFS blocks:", dfs_filtered)
          
            # Add all information to functions_info
            functions_info.append((function[0], hex(function[2]), assembly_code, address, bytecodes, bfs_filtered, dfs_filtered))
                        
        # Verify and replace empty values in functions_info
        functions_info_checked = []
        for function in functions_info:
            function_name = function[0] if function[0] else "NULL"
            function_entry_point = function[1] if function[1] else "NULL"
            address = function[3] if function[3] else "NULL"
            assembly_code = function[2] if function[2] else "NULL"
            bytecodes = function[4] if function[4] else "NULL"
            bfs_result = json.dumps(function[5]) if function[5] else "NULL"
            dfs_result = json.dumps(function[6]) if function[6] else "NULL"
            functions_info_checked.append((function_name, function_entry_point, address, assembly_code, bytecodes, bfs_result, dfs_result))

        # Print and format the call graph for database insertion
        call_graph_str = ""
        call_graph_str_cleaned = ""
        if call_graph:
            call_graph_str = "\n".join([f" - 0x{edge[0]:x} -> 0x{edge[1]:x}" for edge in call_graph])
            print("\nCall Graph:")
            print(call_graph_str)
            call_graph_str_cleaned = call_graph_str.replace("\n", "")

        # Verify and replace empty values in call_graph_str_cleaned
        call_graph_str_cleaned = call_graph_str_cleaned if call_graph_str_cleaned else "NULL"
        print("\n")
        
        # DATABASE MANAGER----------------------
        db_manager.save_to_db(filename, namef, library, library_version, compiler, compiler_version, architecture, filetype, functions_info_checked, call_graph_str_cleaned)
        db_manager.print_db_info()
        analyzer.close_bridge()

    db_manager.print_db_final()

if __name__ == "__main__":
    main()