import os
import subprocess
import ghidra_bridge
from time import sleep 
#import file
import magic
import networkx as nx
import re

class GhidraFunctionAnalyzer:
    def __init__(self, ghidra_path, filename, projects_path, project_name, server_port, ghidra_scripts_root_path, ghidra_script):
        self.ghidra_path = ghidra_path
        self.filename = filename
        self.projects_path = projects_path
        self.project_name = project_name
        self.server_port = server_port
        self.ghidra_scripts_root_path = ghidra_scripts_root_path
        self.ghidra_script = ghidra_script
        self.project_log = open(os.path.join(self.projects_path, self.project_name + ".log"), "w")
        self.project_log_read = open(os.path.join(self.projects_path, self.project_name + ".log"), "r")

        try:
            self.bg_ghidra_process = self._start_ghidra()
            print("End start function\n")
            self.bridge = self._bind_to_bridge()
            print("Start ghidra_bridge\n")
        except Exception as e:
            print(f"Error during Ghidra startup: {e}")
            self._handle_exception_during_startup()

    def _start_ghidra(self):
        ghidrassss = os.path.join(self.ghidra_path, "support")
        ghidra_exe = os.path.join(ghidrassss, "analyzeHeadless")
        print(ghidra_exe)
        process_statement = [ghidra_exe, self.projects_path, self.project_name, "-import", self.filename, "-scriptPath", self.ghidra_scripts_root_path, "-postScript", self.ghidra_script, str(self.server_port)]
        print(" ".join(process_statement))
        process = subprocess.Popen(process_statement, shell=False, stdout=self.project_log, stderr=self.project_log)

        print("Start the count for the timeout\n")
        max_timeout = 900
        while(True):
            new_lines = self.project_log_read.readlines()
            
            for line in new_lines:
                if "Traceback (most recent call last)" in line:
                    raise Exception("There was an exception starting ghidra analysis")
                elif "INFO:jfx_bridge.bridge:serving!" in line:
                    return process

            if process.poll() is not None:
                raise Exception("Process terminated unexpectedly")

            max_timeout -= 1
            if max_timeout > 0:
                sleep(1)
            else:
                raise Exception("After 900 seconds ghidra didn't finish the analysis")

    def _bind_to_bridge(self, response_timeout=10000):
        return ghidra_bridge.GhidraBridge(namespace=globals(), connect_to_port=self.server_port, response_timeout=response_timeout)

    def close_bridge(self):
        self.bridge.remote_shutdown()

        max_timeout = 60
        while(True):
            new_lines = self.project_log_read.readlines()
            
            for line in new_lines:
                if "Traceback (most recent call last)" in line:
                    raise Exception("There was an exception closing ghidra analysis")
                elif "Save succeeded for file" in line:
                    return True

            if self.bg_ghidra_process.poll() is not None:
                return True

            max_timeout -= 1
            if max_timeout > 0:
                sleep(1)
            else:
                self.bg_ghidra_process.kill()
                return True

    def _handle_exception_during_startup(self):
        """Handles exceptions during the startup of Ghidra by removing the problematic file."""
        print(f"Removing problematic file: {self.filename}")
        os.remove(self.filename)  # Remove the file that caused the issue

    def get_file_name(self):
        # Prints the library name to the screen based on the loaded program
        file_name = self.bridge.remote_eval("currentProgram.getName()")
        return file_name

    def get_function_list(self):
        return list(self.bridge.remote_eval("[ [f.getName(), f.getName(True), f.getEntryPoint(), f] for f in currentProgram.getFunctionManager().getFunctions(True) ]"))

    # FOR TEST NOT ACTIVATE; PROBLEMS WITH IMPORT MAGIC NON WINDOWS LIBRARY
    def get_file_type(self, filename):
        try:
            # Run the 'file' command and get the output
            result = subprocess.run(['file', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            #  Decode the output into string format
            output = result.stdout.decode('utf-8')
            # Extracts the file type from the output string
            file_type = output.split(":")[1].strip().split(",")[0]
            return file_type
        except subprocess.CalledProcessError:
            print("Error when retrieving file type.")
            return None

    def get_call_graph(self):
        edges = []
        functions = self.get_function_list()
        functions = [function for function in functions if "<EXTERNAL>" not in function[1]]

        for function in functions:
            called_functions = list(self.bridge.remote_eval("[ [c.getName(), c.getName(True), c.getEntryPoint(), c] for c in f.getCalledFunctions(getMonitor()) ]", f=function[3]))
            called_functions = [c_function for c_function in called_functions if "EXTERNAL" not in c_function[1]]
            for c_function in called_functions:
                edges.append((int(function[2].toString(), 16), int(c_function[2].toString(), 16)))

        functions = list(map(lambda x: x[:2] + [int(x[2].toString(), 16)], functions))
        return functions, edges

    #-------------------------------------------------------------------------#

    # Inizializying external libraries to takes assembly from function
    def setup_code_unit_format(self):
        remote_listing_module = self.bridge.remote_import("ghidra.program.model.listing")
        remote_symbol_module = self.bridge.remote_import("ghidra.program.model.symbol")
        remote_template_module = self.bridge.remote_import("ghidra.app.util.template")

        CodeUnitFormat = remote_listing_module.CodeUnitFormat
        CodeUnitFormatOptions = remote_listing_module.CodeUnitFormatOptions
        RefType = remote_symbol_module.RefType

        templateSimplifier = remote_template_module.TemplateSimplifier()
        codeUnitFormatOptions = CodeUnitFormatOptions(CodeUnitFormatOptions.ShowBlockName.ALWAYS, CodeUnitFormatOptions.ShowNamespace.ALWAYS, "", True, True, True, True, True, True, True, templateSimplifier)
        codeUnitFormat = CodeUnitFormat(codeUnitFormatOptions)

        return codeUnitFormat

    # Stop when find ret opcode in the function assembly code
    # Adding last_address to perform control to stopping block search, you can remove it if not useful
    def get_assembly_functions_ret_stop(self, start_address):
        # Imports modules and configure the visualization info
        codeUnitFormat = self.setup_code_unit_format()
        addr = toAddr(start_address)
        instructions = []
        addresses = []
        bytecodes = []  
        last_address = None  
    
        if addr is None:
            return instructions, addresses, bytecodes, last_address  # Exit if null
    
        instruction = currentProgram.getListing().getInstructionAt(addr)
        while instruction is not None:  
            address = instruction.getAddress()
            address_str = "{}".format(address)  # Convert the address into a string
            instruction_string = codeUnitFormat.getRepresentationString(instruction)
            
            # Get instruction bytes
            instruction_bytes = instruction.getBytes()
            # Construct bytecodes string without any separation
            bytes_string = ''.join(['{:02X}'.format(b & 0xFF) for b in instruction_bytes])
            
            print("{} -> {} -> {}".format(address_str, instruction_string, bytes_string))  # Print address, instruction, and bytecode
            
            instructions.append(instruction_string)
            addresses.append(address_str)
            bytecodes.append(bytes_string)
            
            # Check if the current instruction is a 'ret' instruction
            if instruction.getMnemonicString() == "ret":
                last_address = address_str
                print("Last Address Found:", last_address, "Type:", type(last_address))
                break  # Exit the loop if 'ret' instruction is encountered
    
            instruction = instruction.getNext()
    
        return instructions, addresses, bytecodes, last_address  

    # Regex convert type in string
    def extract_address(self, last_address):
        match = re.search(r'\b([0-9a-fA-F]+)\b', str(last_address))
        if match:
            return match.group(0)
        else:
            return None

    # Initializing functions from ghidra to use to takes blocks for CFG
    def load_ghidra_libraries(self):
        remote_listing_module = self.bridge.remote_import("ghidra.program.model.listing")
        remote_symbol_module = self.bridge.remote_import("ghidra.program.model.symbol")
        remote_block_module = self.bridge.remote_import("ghidra.program.model.block")
        remote_task_module = self.bridge.remote_import("ghidra.util.task")

        return remote_listing_module, remote_symbol_module, remote_block_module, remote_task_module

    def print_blocks_function(self, start_address):
        remote_listing_module, _, remote_block_module, remote_task_module = self.load_ghidra_libraries()
        CodeUnitFormat = remote_listing_module.CodeUnitFormat

        addr = toAddr(start_address)

        if addr is None:
            return

        code_block_model = remote_block_module.SimpleBlockModel(currentProgram)
        blocks = code_block_model.getCodeBlockAt(addr, remote_task_module.TaskMonitor.DUMMY)

        for block in blocks:
            if isinstance(block, remote_block_module.CodeBlock):
                print("it's a block", block)
            else:
                print("The block is not of type block:", block)
    
                # If the block is not of type block, we create a new block of code using the start and end addresses.                start = block.getMinAddress()
                end = block.getMaxAddress()
                print("Block start address:", start)
                print("Block end address:", end)

    # Disuses, used to check the first block address, if matches with previous printed address
    def get_first_function_block(self, start_address):
        remote_listing_module, _, remote_block_module, remote_task_module = self.load_ghidra_libraries()
    
        addr = toAddr(start_address)
    
        if addr is None:
            return None  # Return None if null address
    
        code_block_model = remote_block_module.SimpleBlockModel(currentProgram)
        first_block = code_block_model.getFirstCodeBlockContaining(addr, remote_task_module.TaskMonitor.DUMMY)
    
        return first_block

    # OPTIMIZED
    def CFG_and_destinationblocks_ricorsiva(self, start_address, last_address_str=None, print_result=True):
        remote_listing_module, _, remote_block_module, remote_task_module = self.load_ghidra_libraries()
        CodeUnitFormat = remote_listing_module.CodeUnitFormat

        addr = toAddr(start_address)
        last_address = toAddr(last_address_str) if last_address_str else None

        if addr is None:
            print("Null address, esc")
            return {} if not print_result else None

        code_block_model = remote_block_module.SimpleBlockModel(currentProgram)
        print("Here is the address that will identify this block", addr)
        blocks = code_block_model.getCodeBlocksContaining(addr, remote_task_module.TaskMonitor.DUMMY)

        # Recursive function to retrieve destination blocks
        def collect_destination_blocks(current_block, visited_blocks, result):
            if current_block in visited_blocks:
                visited_blocks[current_block] += 1  # Increase the counter for single block
                return
            visited_blocks[current_block] = 1  # Initialize the counter for the block at 1

            destinations = code_block_model.getDestinations(current_block, remote_task_module.TaskMonitor.DUMMY)
            destination_list = []

            while destinations.hasNext():
                destination = destinations.next()
                dest_address = destination.getDestinationAddress()

                # Filter by start_address and last_address if last_address is provided
                if last_address and (dest_address < addr or dest_address > last_address):
                    continue

                destination_block = code_block_model.getCodeBlockAt(dest_address, remote_task_module.TaskMonitor.DUMMY)

                if destination_block:
                    destination_list.append(destination_block)
                    # Recursively collect the destination blocks of the destination blocks
                    collect_destination_blocks(destination_block, visited_blocks, result)

            result[current_block] = destination_list

        result = {}
        visited_blocks = {}
        # Collect target blocks for each current block
        for block in blocks:
            if not last_address or block.getFirstStartAddress() <= last_address:  # Filter by last_address if provided
                collect_destination_blocks(block, visited_blocks, result)

        # Creating a dictionary that contains blocks and their corresponding destination blocks
        result_dict = {}
        for block, destinations in result.items():
            destination_names = [str(dest.getFirstStartAddress()) for dest in destinations]
            result_dict[str(block.getFirstStartAddress())] = destination_names

        if print_result:
            # Print the result
            for block, destinations in result.items():
                destination_names = ", ".join(str(dest.getFirstStartAddress()) for dest in destinations)
                cycle_count = visited_blocks.get(block.getFirstStartAddress(), 0)  # Get the visit count for this block
                print(f"{block.getFirstStartAddress()} -> destination blocks({destination_names}), visited {cycle_count} times")

        return result_dict

    def confronta_blocchi(self, graph, last_address, starting_node):
        try:
            bfs_filtered = []
            for blocco in graph:
                if blocco < last_address and blocco >= starting_node:
                    bfs_filtered.append(blocco)
            return bfs_filtered
        except Exception as e:
            # Log the exception if necessary, e.g., print(e)
            return []

